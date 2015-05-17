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
     print(addr)
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

def go(sp):
     sp.write(chr(0x05))
     write=sys.stdout.write
     while True:
          write(sp.read())

def send_int(sp, x):
     sum = 0
     for i in xrange(0, 4):
          sp.write(chr(x&0xff))
          sum += x & 0xff
          x >>= 8
     return sum

def read_info(sp, n=0):
    temp=sp.read()
    cnt = 1
    while ord(temp)!=0x15:
        sys.stdout.write(temp)
        if cnt==n:
            break
        temp=sp.read()
        cnt += 1
    print('')

def  peek(sp, pos):
     sp.flushInput()
     pos = eval(pos)
     sum = 2
     sp.write(chr(0x02))
     sum += send_int(sp, pos)
     sp.write(chr(sum&0xff))
     sp.flush()
     temp=sp.read()
     if ord(temp)!=0x06:
         print('error')
     else:
          read_info(sp, 8)

def poke(sp, pos, data):
     pos = eval(pos)
     data = eval(data)
     sum = 3
     sp.write(chr(0x03))
     sum += send_int(sp, pos)
     sum += send_int(sp, data)
     sp.write(chr(sum&0xff))
     sp.flush()
     temp = sp.read()
     if ord(temp)!=0x06:
          print('error')

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

     sp = open(conf['port'], conf['baud'])

     print conf['port']
     print conf['baud']

     read_info(sp)

     while True:
          sys.stdout.write('$')
          cmd = raw_input()
          args = cmd.split();
          if len(args) == 2 and args[0] == 'load':
               load_data(sp, args[1])
          elif len(args) == 1 and args[0] == 'go':
               go(sp)
          elif len(args) == 2 and args[0] == 'peek':
               peek(sp, args[1])
          elif len(args) == 3 and args[0] == 'poke':
               poke(sp, args[1], args[2])
          elif  len(args) == 2 and args[0] == 'verify':
               load_data(sp, args[1], 1)

     sp.close()
