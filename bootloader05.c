
//-------------------------------------------------------------------------
//-------------------------------------------------------------------------

// The raspberry pi firmware at the time this was written defaults
// loading at address 0x8000.  Although this bootloader could easily
// load at 0x0000, it loads at 0x8000 so that the same binaries built
// for the SD card work with this bootloader.  Change the ARMBASE
// below to use a different location.

#define ARMBASE 0x8000

extern void PUT32 ( unsigned int, unsigned int );
extern void PUT16 ( unsigned int, unsigned int );
extern void PUT8 ( unsigned int, unsigned int );
extern unsigned int GET32 ( unsigned int );
extern unsigned int GETPC ( void );
extern void BRANCHTO ( unsigned int );
extern void dummy ( unsigned int );

extern void uart_init ( void );
extern unsigned int uart_lcr ( void );
extern void uart_flush ( void );
extern void uart_send ( unsigned int );
extern unsigned int uart_recv ( void );
extern void hexstring ( unsigned int );
extern void hexstrings ( unsigned int );
extern void timer_init ( void );
extern unsigned int timer_tick ( void );

extern void timer_init ( void );
extern unsigned int timer_tick ( void );

//------------------------------------------------------------------------
unsigned char xstring[256];
//------------------------------------------------------------------------

unsigned int get_int(unsigned int state)
{
    return (unsigned int)xstring[state]<<24|(unsigned int)xstring[state-1]<<16|(unsigned int)xstring[state-2]<<8|xstring[state-3];
}

void print_info(char *s)
{
    for (; *s; ++s)
		uart_send(*s);
}

int notmain ( void )
{
    unsigned int ra;
    //unsigned int rb;
    unsigned int rx;
    unsigned int addr;
    unsigned int block;
    unsigned int state;

    unsigned int pos;
    unsigned int val;

    unsigned int crc;

    unsigned int veri, same;

    uart_init();
    hexstring(0x12345678);
    hexstring(GETPC());
    hexstring(ARMBASE);
    timer_init();

//SOH 0x01
//ACK 0x06
//NAK 0x15
//EOT 0x04

//block numbers start with 1

//132 byte packet
//starts with SOH
//block number byte
//255-block number
//128 bytes of data
//checksum byte (whole packet)
//a single EOT instead of SOH when done, send an ACK on it too

    block=1;
    addr=ARMBASE;
    state=0;
    crc=0;
    rx=timer_tick();
    veri=0;
    while(1)
    {
        ra=timer_tick();
        if((ra-rx)>=2000000)
        {
            state=0;
            uart_send(0x15);
            rx+=2000000;
        }
        if((uart_lcr()&0x01)==0) continue;
        xstring[state]=uart_recv();
        rx=timer_tick();

        switch(state)
        {
            case 0:
            {
                crc=xstring[state];
                switch(xstring[state]){
                    case 0x01: //load a block
                    {
                        state=2;
                        break;
                    }
                    case 0x02: //peek
                    {
                        state=132;
                        break;
                    }
                    case 0x03: //poke
                    {
                        state=137;
                        break;
                    }
                    case 0x04: //finish sending
                    {
                        addr=ARMBASE;
                        block=1;
                        veri=0;
                        uart_send(0x06);
                        uart_flush();
                        state=0;
                        break;
                    }
                    case 0x05: //go
                    {
                        uart_send(0x06);
                        for(ra=0;ra<30;ra++) hexstring(ra);
                        hexstring(0x11111111);
                        hexstring(0x22222222);
                        hexstring(0x33333333);
                        uart_flush();
                        BRANCHTO(ARMBASE);
                        break;
                    }
                    case 0x06: //verify
                    {
                        addr=ARMBASE;
                        block=1;
                        veri=1;
                        state=0;
                        break;
                    }
                    case 0x07: //start sending
                    {
                        addr=ARMBASE;
                        block=1;
                        veri=0;
                        state=0;
                        break;
                    }
                    default:
                        uart_send(0x15);
                }
                break;
            }

            case 1:
            {
                if(xstring[state]==block)
                {
                    crc+=xstring[state];
                    state++;
                }
                else
                {
                    state=0;
                    uart_send(0x15);
                }
                break;
            }

            case 2:
            {
                if(xstring[state]==(0xFF-xstring[state-1]))
                {
                    crc+=xstring[state];
                    state++;
                }
                else
                {
                    uart_send(0x15);
                    state=0;
                }
                break;
            }

            case 131:
            {
                crc&=0xFF;
                if(xstring[state]==crc)
                {
                    if(!veri){
                        for(ra=0;ra<128;ra++)
                        {
                            PUT8(addr++,xstring[ra+3]);
                        }
                    }
                    else
                    {
                        same=1;
                        for(ra=0;ra<128;ra++)
                        {
                            val=GET32(addr++)&0xff;
                            same=same&&(val==xstring[ra+3]);
                        }
                    }
                    uart_send(0x06);
                    block=(block+1)&0xFF;
                    if(veri)uart_send(same); //send the result of verification
                }
                else
                {
                    uart_send(0x15);
                }
                uart_flush();
                state=0;
                break;
            }
            
            case 136: //peek
            {
                crc&=0xff;
                if(crc==xstring[state])
                {
                    state--;
                    pos = get_int(state);
                    val = GET32(pos);
                    uart_send(0x06);
                    print_info("address: ");
                    hexstring(pos);
                    print_info("value: ");
                    hexstring(val);
                }
                else
                {
                    uart_send(0x15);
                }
                uart_flush();
                state=0;
                break;
            }

            case 145: //poke, read val
            {
                crc&=0xff;
                if(crc==xstring[state])
                {
                    state--;
                    pos = get_int(state-4);
                    val = get_int(state);
                    uart_send(0x06);
                    print_info("address: ");
                    hexstring(pos);
                    print_info("old value: ");
                    hexstring(GET32(pos));
                    PUT32(pos, val);
                    print_info("new value: ");
                    hexstring(GET32(pos));
                }
                else
                {
                    uart_send(0x15);
                }
                uart_flush();
                state=0;
                break;
            }

            default:
            {
                crc+=xstring[state];
                state++;
                break;
            }
        }
    }
    return(0);
}
//-------------------------------------------------------------------------
//-------------------------------------------------------------------------


//-------------------------------------------------------------------------
//
// Copyright (c) 2012 David Welch dwelch@dwelch.com
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//
//-------------------------------------------------------------------------
