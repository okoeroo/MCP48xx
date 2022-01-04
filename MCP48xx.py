from machine import SPI, Pin

### The selection of the model indicates the
### amount of bits resolution it can handle

class TYPE_OF_MCP48xx(object):
    MCP4822 = 12
    MCP4812 = 10
    MCP4802 = 8


class MCP48XX(object):
    # The write command is initiated by driving the CS pin low,
    # followed by clocking the four Configuration bits and the
    # 12 data bits into the SDI pin on the rising edge of SCK.

    # The CS pin is then raised, causing the data to be latched
    # into the selected DAC’s input registers.

    # The MCP4802/4812/4822 devices utilize a double- buffered
    # latch structure to allow both DACA’s and DACB’s outputs
    # to be synchronized with the LDAC pin, if desired.

    # By bringing down the LDAC pin to a low state, the contents
    # stored in the DAC’s input registers are transferred into
    # the DAC’s output registers (VOUT), and both VOUTA and VOUTB
    # are updated at the same time.

    # All writes to the MCP4802/4812/4822 devices are 16-bit words.
    # Any clocks after the first 16th clock will be ignored.

    # The most Significant four bits are Configuration bits.
    # The remaining 12 bits are data bits. No data can be transferred
    # into the device with CS high. The data transfer will only occur
    # if 16 clocks have been transferred into the device. If the
    # rising edge of CS occurs prior, shifting of data into the
    # input registers will be aborted.

    # A gain of low will give a voltage between 0 and 2.047 volts.
    # A gain of high will give a voltage between 0 and 3.3 volts.

    # 15: Channel select: 1 = B, 0 = A
    # 14: ignored
    # 13: Gain: 1: 1x (VOUT = VREF * D/4096),
    #           0: 2x (VOUT = 2 * VREF * D/4096),
    #                 where internal VREF = 2.048V.
    # 12: Shutdown: 1: Active mode,
    #               0: Shutdown the selected DAC channel.
    #                  Analog output is not available at
    #                  the channel that was shut down.
    #                  VOUT pin is connected to 500 kOHM typical)
    # 11-0: data bits

    self.HIGH = 1
    self.LOW  = 0

    self.CHAN_B = 1
    self.CHAN_A = 0

    def __init__(self, model, spi_id, cs, sck_pin, mosi_pin, miso_pin):
        self.chipselect = cs
        self.chipselect_pin = Pin(cs, Pin.OUT)

        self.spi_id = spi_id

        # Model filter
        if model != TYPE_OF_MCP48xx.MCP4822 or
            model != TYPE_OF_MCP48xx.MCP4812 or
            model != TYPE_OF_MCP48xx.MCP4802:
            raise ValueError("Not a valid type, use MCP4822, MCP4812, MCP4802")

        # The write command consists of 16 bits and is
        # used to configure the DAC’s control and data latches
        self.data_A = bytearray(2)
        self.data_B = bytearray(2)

        self.model = model
        self.max = 2 ** self.model

        self.on_A = False
        self.on_B = False

        self.gain_A = False
        self.gain_B = False

        self.raw_value_A = 0
        self.raw_value_B = 0

        self.sck  = Pin(sck_pin)
        self.mosi = Pin(mosi_pin)
        self.miso = Pin(miso_pin)

        # First stage
        self.chipSelectHigh()
        self.spi =  SPI(self.spi_id,
                        baudrate=400000,
                        sck = self.sck,
                        mosi = self.mosi,
                        miso = self.miso)

    def updateDAC(self):
        self.updateDAC_per_chan(self.CHAN_A)
        self.updateDAC_per_chan(self.CHAN_B)

    def updateDAC_per_chan(self, channel):
        buf = bytearray(2)

        if channel == self.CHAN_B:
            buf[1] |= 2**7     # Set channel B
            if self.gain_B:
                buf[1] |= 2**5
            if self.on_B:
                buf[1] |= 2**4

            buf[1] |= self.raw_value_B >> 8 & 15
            buf[0] |= self.raw_value_B

            self.dataB = buf
        else:
            if self.gain_A:
                buf[1] |= 2**5
            if self.on_A:
                buf[1] |= 2**4

            buf[1] |= self.raw_value_A >> 8 & 15
            buf[0] |= self.raw_value_A

            self.dataA = buf

        ### Write buffer to SPI
        try:
            self.chipSelectLow()
            self.spi.write(buf)
        finally:
            self.chipSelectHigh()

    def chipSelectHigh(self):
        self.chipselect_state = self.HIGH
        self.chipselect_pin.on()

    def chipSelectLow(self):
        self.chipselect_state = self.LOW
        self.chipselect_pin.off()

    def setValue(self, value):
        self.raw_value_A = value

    def setValue(self, value):
        self.raw_value_B = value

    def turnOnChannelA(self):
        self.on_A = True

    def turnOnChannelB(self):
        self.on_B = True

    def shutdownChannelA(self):
        self.on_A = False

    def shutdownChannelB(self):
        self.on_B = False

    def setGainA(self):
        self.gain_A = True

    def setGainB(self):
        self.gain_B = True


