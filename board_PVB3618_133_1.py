import time

BOARDNAME = "PVB3618-133-1"
ECXNAME = "ECX337A"
PINS = [
    {
        "PWR": 35,
        "XSCK": 201,
        "XCS": 202,
        "XCLR": 203,
        "SO": 206,
        "SI": 207,
    }
]
NUM_DISPLAYS = len(PINS)


def hw_export(pin):
    with open("/sys/class/gpio/export", 'w') as fd:
        fd.write(str(pin))
        
def hw_direction(pin, direction):
    with open("/sys/class/gpio/gpio" + str(pin) + "/direction", 'w') as fd:
        fd.write(str(direction))
        
def hw_write(pin, value):
    with open("/sys/class/gpio/gpio" + str(pin) + "/value", 'w') as fd:
        fd.write(str(value))
        
def hw_read(pin):
    with open("/sys/class/gpio/gpio" + str(pin) + "/value", 'r') as fd:
        return int(fd.read()[:-1])


def ecx_begin(pinset):
    time.sleep(200e-6)
    hw_write(pinset["XCS"], 0)
    time.sleep(200e-6)
    
def ecx_end(pinset):
    time.sleep(200e-6)
    hw_write(pinset["XCS"], 1)
    time.sleep(200e-6)
    
def ecx_shift(pinset, data, rd=False):
    indata = 0x00
    for i in range(8):
        hw_write(pinset["SI"], 1 if data & (1 << i) else 0)
        time.sleep(5e-6)
        hw_write(pinset["XSCK"], 1)
        if rd:
            indata = (indata << 1) | hw_read(pinset["SO"])
        time.sleep(5e-6)
        hw_write(pinset["XSCK"], 0)
    return indata
    
def ecx_burst(pinset, data):
    ecx_begin(pinset)
    for byte in data:
        ecx_shift(pinset, byte)
    ecx_end(pinset)
    
def ecx_comm(pinset, addr, byte, rd=False):
    ecx_begin(pinset)
    ecx_shift(pinset, addr)
    res = ecx_shift(pinset, byte, rd=rd)
    ecx_end(pinset)
    return res
    
    
def init(idx):
    pinset = PINS[idx]
    
    try:
        for name, pin in pinset.items():
            hw_export(pin)
    except:
        pass
    
    hw_direction(pinset["PWR"], "high")
    hw_direction(pinset["XSCK"], "low")
    hw_direction(pinset["XCS"], "high")
    hw_direction(pinset["XCLR"], "low")
    hw_direction(pinset["SO"], "in")
    hw_direction(pinset["SI"], "low")
    
    time.sleep(16e-3)
    hw_write(pinset["XCLR"], 1)
    time.sleep(16e-3)
    
    ecx_comm(pinset, 0x80, 0x01)
    ecx_comm(pinset, 0x81, 0x7F)
    res = ecx_comm(pinset, 0x81, 0x00, rd=True)
    ecx_comm(pinset, 0x80, 0x00)
    
    if res == 0x56:
        ecx_burst([
            0x01,
            0x00,
            0x80,
            0x0B, # PRTSWP set
        ])
        return 0
    else:
        print(ECXNAME, "#"+str(idx), "probe failed:", hex(res))
        return -1
    
def poweron(idx):
    pinset = PINS[idx]
    
    hw_write(pinset["PWR"], 0)
    time.sleep(16e-3)
    
def poweroff(idx):
    pinset = PINS[idx]
    
    time.sleep(16e-3)
    hw_write(pinset["PWR"], 1)

def panelon(idx):
    pinset = PINS[idx]
    
    ecx_comm(pinset, 0x00, 0x4D)
    ecx_comm(pinset, 0x00, 0x4F)

def paneloff(idx):
    pinset = PINS[idx]
    
    ecx_comm(pinset, 0x00, 0x4D)
    ecx_comm(pinset, 0x00, 0x4C)

def brightness(idx, percent):
    pinset = PINS[idx]
    
    percent = max(percent, 5)
    percent = min(percent, 100)
    ecx_comm(pinset, 0x11, 0x07)
    ecx_comm(pinset, 0x13, percent)
    
