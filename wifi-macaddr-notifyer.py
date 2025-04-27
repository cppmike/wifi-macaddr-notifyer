import time
import scapy.all as scapy
import asyncio
from telegram import Bot
from datetime import datetime, timedelta

# settings
TARGET_MACS = ["aa:aa:aa:aa:aa:aa", "bb:bb:bb:bb:bb:bb", "cc:cc:cc:cc:cc:cc", "dd:dd:dd:dd:dd:dd"]  # your MAC-addresses devices
BOT_TOKEN = "YOUR_BOT_TOKEN"  
CHAT_ID = "YOUR_CHAT_ID"
NOTIFICATION_COOLDOWN = timedelta(hours=4)  # Notification interval (4 hours)

# scanning the network
def scan_network(ip_range):
    arp_request = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    clients_list = []
    for element in answered_list:
        client_dict = {"ip": element[1].psrc, "mac": element[1].hwsrc}
        clients_list.append(client_dict)
    return clients_list

# sending notification in Telegram
async def send_telegram_notification(message):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message)

async def main():
    ip_range = "192.168.1.1/24"  # your network's IP range
    connected_devices = set()  
    last_notification_time = {}  

    while True:
        clients = scan_network(ip_range)
        current_connected_devices = set() 

        # Checking current connections
        for client in clients:
            if client["mac"] in TARGET_MACS:
                current_connected_devices.add(client["mac"])

                # If the device is connected for the first time (was not in connected_devices)
                if client["mac"] not in connected_devices:
                    print(f"New device discovered: {client['mac']}")
                    connected_devices.add(client["mac"])
                    
                    # Check when a notification was last sent for this device
                    last_notification = last_notification_time.get(client["mac"])
                    now = datetime.now()

                    # If the notification has not been sent yet or more than 4 hours have passed
                    if last_notification is None or now - last_notification >= NOTIFICATION_COOLDOWN:
                        await send_telegram_notification(f"Device with mac address {client['mac']} connected to the network!")
                        last_notification_time[client["mac"]] = now

        # Checking which devices have been disconnected
        for mac in connected_devices.copy():
            if mac not in current_connected_devices:
                print(f"Device disconnected: {mac}")
                connected_devices.discard(mac) 

        time.sleep(10)  # Pause between scans

if __name__ == "__main__":
    asyncio.run(main())
