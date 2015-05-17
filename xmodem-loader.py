#Need to install the PySerial library first

import sys, getopt
import serial
import time

def open(aport='/dev/ttyUSB0', abaudrate=115200) :
     return serial.Serial(
          port=aport,
          baudrate=abaudrate,     # baudrate
          bytesize=8,             # number of databits
          parity=serial.PARITY_NONE,
          stopbits=1,
          xonxoff=0,              # enable software flow control
          rtscts=0,               # disable RTS/CTS flow control
          timeout=None            # set a timeout value, None for waiting forever
     )

def load_data(sp, addr, verify=False):
     data = map(lambda c: ord(c), file(addr,"rb").read())
     temp = sp.read()
     buf = ""

     while ord(temp)!=0x15:
          buf += temp
          temp = sp.read()

     print(buf)

     dataLength = len(data)
     blockNum = (dataLength-1)/128+1
     print "The size of the image is ",dataLength,"!"
     print "Total block number is ",blockNum,"!"
     print "Download start,",blockNum,"block(s) in total!"

     for i in range(1,blockNum+1):
          success = False

          while success == False:
               sp.write(chr(0x01))
               sp.write(chr(i&0xFF))
               sp.write(chr(0xFF-i&0xFF))
               crc = 0x01+0xFF
         
               for j in range(0,128):
                    if len(data)>(i-1)*128+j:
                         sp.write(chr(data[(i-1)*128+j]))
                         crc += data[(i-1)*128+j]
                    else:
                         sp.write(chr(0xff))
                         crc += 0xff

               crc &= 0xff
               sp.write(chr(crc))
               sp.flush()
               temp=sp.read()
               sp.flushInput()

               if ord(temp)==0x06:
                    success = True
                    print "Block",i,"has finished!"
               else:
                    print "Error,send again!"

     sp.write(chr(0x04))
     sp.flush()
     temp=sp.read()

     if ord(temp)==0x06:
          print "Download has finished!"

     sp.read(33*11-3)

def go(sp):
     sp.write(chr(0x05))
     write=sys.stdout.write
     while True:
          write(sp.read())

def send_int(sp, x):
     t=4;
     while t>0:
          sp.send(chr(x&0xff))
          x >>= 8
          t -= 1;

def  peek(sp, pos):
     pos = eval(pos)
     send_int(sp, pos)
     sys.stdout.write(sp.read(4))


def poke(sp, pos, data):
     pos = eval(pos)
     data = eval(data)
     send_int(sp, pos)
     send_int(sp, data)

if __name__ == "__main__":

     # Import Psyco if available
     try:
          import psyco
          psyco.full()
          print "Using Psyco..."
     except ImportError:
          pass

     conf = {
          'port': '/dev/ttyUSB0',
          'baud': 115200,
     }

     try:
          opts, args = getopt.getopt(sys.argv[1:], "hqVewvrp:b:a:l:")
     except getopt.GetoptError, err:
          print str(err) 
          sys.exit(2)
        
     for o, a in opts:
          if o == '-p':
               conf['port'] = a
          elif o == '-b':
               conf['baud'] = eval(a)
          else:
               assert False, "unhandled option"

     #sp = open(conf['port'], conf['baud'])

     print args[0]
     print conf['port']
     print conf['baud']


     while True:
          cmd = raw_input()
          args = cmd.split();
          print(args)
          if len(args) == 2 and args[0] == 'load':
               load_data(sp, args[1])
          elif len(args) == 1 and args[0] == 'go':
               go(sp)
          elif len(args) == 2 and args[0] == 'peek':
               peek(sp, args[1])
          elif len(args) == 3 and args[0] == 'poke':
               poke(sp, args[1], args[2])
          elif  len(args) == 2 and args[0] == 'verify':
               verify(sp, args[1])

     sp.close()
