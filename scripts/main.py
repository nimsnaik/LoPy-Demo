from network import LoRa
from machine import Pin
import socket
import time
import binascii
import pycom
import struct

# stop LED heartbeat
pycom.heartbeat(False)
pycom.rgbled(0x000000)           # turn off LEDs

# Initialize LoRa in LORAWAN mode.
lora = LoRa(mode=LoRa.LORAWAN)

# create an OTAA authentication parameters
app_eui = binascii.unhexlify('a4bb564dd72a29c1'.replace(' ',''))
app_key = binascii.unhexlify('235ec3907acfe735b0ed665882903526'.replace(' ',''))

# app_eui = binascii.unhexlify('70B3D57ED001D04F')
# app_key = binascii.unhexlify('39B1A172592EF0FF54B83D2D7A026FEB')

# Get the DevEUI from the node
print('DevEUI ', binascii.hexlify(lora.mac()))

# Quick Join in the US
for i in range(8, 72):
    print("Remove channel from search: ", i)
    lora.remove_channel(i)


# join a network using OTAA (Over the Air Activation)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(1.0)
    pycom.rgbled(0x7f0000)           # blink RED led during join
    print('Not yet joined...')
    time.sleep(0.25)
    pycom.rgbled(0x000000)           # turn LED off

# # wait until the module has joined the network
# while not lora.has_joined():
#     pycom.rgbled(0x00007f)
#     time.sleep(2.5)
#     pycom.rgbled(0x000000)
#     print('Not joined yet...')

print('Network joined!')


# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# selecting confirmed type of messages
s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

# set the LoRaWAN data rate
#s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)




cnt = 0
pycom.rgbled(0x000000)           # turn off

button = Pin("P14", mode=Pin.IN, pull=Pin.PULL_UP)
is_pressed = False

while True:
    # make the socket blocking
    # (waits for the data to be sent and for the 2 receive windows to expire)
    if button() == 1 and not is_pressed:
        time.sleep(1)
    elif button() == 0 and not is_pressed:
        #print("Button pressed")
        is_pressed = True
    elif button() == 1 and is_pressed:
        #print("Button released")
        is_pressed = False
    else:
        pass

    pycom.rgbled(0x007f00)           # turn on the green LED

    try:
        s.setblocking(True)
        # send some data
        if(is_pressed):
            s.send(bytes([cnt, 1, 0]))
        else:
            s.send(bytes([cnt, 0, 0]))
        print( cnt, ' Sending...' )

    except Exception as e:
        if e.args[0] == 11:
            print('cannot send just yet, waiting...')
            time.sleep(2.0)
        else:
            raise    # raise the exception again

    pycom.rgbled(0x000000)           # turn off the green LED

    # make the socket non-blocking
    # (because if there's no data received it will block forever...)
    s.setblocking(False)
    # get any data received (if any...)
    data = s.recv(64)
    if data:
        pycom.rgbled(0x00007f)           # turn on the RED LED
        print( 'Got:')
        rgbval = struct.unpack('<i', data)
        print(rgbval[0])
        pycom.rgbled(rgbval[0])
        time.sleep(5)
    else:
        print( 'No Data Received' )
    # saturating add so that count matches uint8 value in payload
    cnt+=1%255
    pycom.rgbled(0x000000)           # turn off LED
    time.sleep(1)
