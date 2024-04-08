# import package
import pyvisa
import time
import serial
from math import *

def Vpp_to_dBm(Vpp):
    return 10*log(2.5*Vpp**2)/log(10)

def dBm_to_Vpp(dBm):
    return sqrt(0.4*10**(dBm/10))



class Appa:
    def __init__(self, port: str):
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=9600,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE
            )
            print("Serial" + port + "connection estabilished")
        except:
            print("Serial" + port + "connection fault")
            if(self.ser.isOpen()):
                self.ser.close()

    def v(self):
        self.ser.write(b"\x55\x55\x01\x00\xab")
        time.sleep(0.5)
        data = self.ser.read(self.ser.inWaiting())
        return float(int.from_bytes(bytearray([data[6],data[7]]), 'little'))/10000
    def close(self):
        self.ser.close()

class Channel:
    def __init__(self,number:int,inst):
        self.n = number
        self.inst = inst
        self._vpp = float(self.q(f":SOURce{self.n}:VOLTage?").strip())
        self._ph = float(self.q(f":SOURce{self.n}:PHASe?").strip())
        self._freq = float(self.q(f":SOURce{self.n}:FREQuency?").strip())
        self.s(":OUTPut1:IMPedance 50")
        self.s(":OUTPut2:IMPedance 50")
        print(f"Channel {number} connected, Z = 50 Ohm, Vpp = {self._vpp} V, Ph = {self._ph} deg, F = {self._freq} Hz")

    @property
    def vpp(self):
        return self._vpp
    @vpp.setter
    def vpp(self, value:float):
        time.sleep(1)
        self._vpp = value
        self.s(f":SOURce{self.n}:VOLTage {value}")
        time.sleep(1)
    @property
    def ph(self):
        return self._ph
    @ph.setter
    def ph(self, value:float):
        time.sleep(1)
        self._ph = value
        self.s(f":SOURce{self.n}:PHASe {value}")
        self.s(f":SOURce{self.n}:PHASe:INITiate")
        time.sleep(1)
    @property
    def freq(self):
        return self._freq
    @freq.setter
    def freq(self, value:int):
        time.sleep(1)
        self._freq = float(value)
        self.s(f":SOURce{self.n}:FREQuency {value}")
        time.sleep(1)
          
    def s(self,command:str):
        time.sleep(0.4)
        self.inst.write(command)
        time.sleep(0.4)

    def q(self,command:str):
        time.sleep(0.4)
        ans = self.inst.query(command)
        time.sleep(0.4)
        return ans
        
    def on(self):
        self.s(f":OUTPut{self.n} ON")

    def off(self):
        self.s(f":OUTPut{self.n} OFF")

    def state(self):
        self._vpp = float(self.q(f":SOURce{self.n}:VOLTage?").strip())
        self._ph = float(self.q(f":SOURce{self.n}:PHASe?").strip())
        self._freq = float(self.q(f":SOURce{self.n}:FREQuency?").strip())
        print(f"Channel {number} state: Vpp = {self._vpp} V, Ph = {self._ph} deg, F = {self._freq} Hz")



class Generator:
    def __init__(self):
        
        self.rm = pyvisa.ResourceManager()
        print(self.rm.list_resources())
        self.port = input("Введите порт генератора из списка или 0 для стандартных настроек:")
        if self.port == "0":
            self.port = 'USB0::0x1AB1::0x0641::DG4E243501816::INSTR'
            self.inst = self.rm.open_resource(self.port)
        else:
            self.inst = self.rm.open_resource(self.port)
        time.sleep(1)
        self.ch1 = Channel(1,self.inst)
        self.ch2 = Channel(2,self.inst)


def Vph(ph):
  return -0.0104876*ph+0.827207


# Connect to waveform generator

gen = Generator()
gen.ch1.ph = 180
gen.ch2.ph = 180
gen.ch1.vpp = dBm_to_Vpp(-30)
gen.ch2.vpp = dBm_to_Vpp(-30)
gen.ch1.freq = 40e6
gen.ch2.freq = 40e6

# Connect to appa multimeters

appa_ph = Appa(input("Введите порт измерителя фазы в формате COMN:"))
appa_mag = Appa(input("Введите порт измерителя амплитуды в формате COMN:"))

gen.ch1.on()
gen.ch2.on()

try:
    data = open("data.txt", "r")
    newdata = open("newdata.txt", "w")
    lines = data.readlines()
    for line in lines:
        array = list(map(float, line.split()))
        Vmag, Vphase, dBm1, dBm2, phase1, phase2 = array
        if((abs(Vph(phase1-phase2)-Vphase)>0.2) and (dBm1>-40)):
            print(array)
            gen.ch1.ph = phase1
            gen.ch1.vpp = dBm_to_Vpp(dBm1)
            line = f"{appa_mag.v()} {appa_ph.v()} {Vpp_to_dBm(gen.ch1.vpp)} {Vpp_to_dBm(gen.ch2.vpp)} {gen.ch1.ph} {gen.ch2.ph}\n"
            newdata.write(line)
            print(line)
        else:
            newdata.write(line)
    appa_mag.close()
    appa_ph.close()
    gen.ch1.off()
    gen.ch2.off()
    data.close()
    newdata.close()
    

except KeyboardInterrupt:
    appa_mag.close()
    appa_ph.close()
    gen.ch1.off()
    gen.ch2.off()
    data.close()
    newdata.close()


except:
    appa_mag.close()
    appa_ph.close()
    gen.ch1.off()
    gen.ch2.off()
    data.close()
    newdata.close()
