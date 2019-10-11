from smbus import SMBus
from time import sleep, time
from threading import Thread
from Adafruit_ADS1x15 import ADS1115
from Adafruit_MAX31855.MAX31855 import MAX31855
from numpy import var, array, asarray, dot, finfo, identity, sqrt, outer, row_stack, mean

static_acc_error = 0

def getPressure(drucksensor_num):
    if drucksensor_num == 5:
        addr = 0x49
        drucksensor_num = 1
    else:
        addr = 0x48

    adc = ADS1115(address=addr)
    GAIN = 1
    # adc.start_adc(drucksensor_num, gain=GAIN)
    valueOfADC = adc.read_adc(drucksensor_num - 1, gain=GAIN)  # abs(adc.get_last_result())
    volt = (valueOfADC / 32767)*4.096
    #bar = round((10 / 3.3) * volt, 2)      # 4-20mA entspricht 0-3.3V
    #bar = round((125/33) * volt - 2.5, 2)   # 0-20mA entspricht 0-3.3V
    bar = round((125/24) * volt -2.5, 2)      # 0-25mA entspricht 0-3V
    return bar

def getTemperature(temperatursensor_num):
    
    if temperatursensor_num == 1:
        CLK = 11
        CS  = 8
        DO  = 9
    elif temperatursensor_num == 2:
        CLK = 11
        CS  = 7
        DO  = 9
    elif temperatursensor_num == 3:
        CLK = 21
        CS = 18
        DO = 19
    elif temperatursensor_num == 4:
        CLK = 21
        CS = 17
        DO = 19
    else:
        CLK = 21
        CS = 16
        DO = 19

    sensor = MAX31855(CLK, CS, DO)
    return sensor.readTempC()

class beschleunigungssensor():
    def __init__(self):
        self.addr = 0x50
        self.i2c = SMBus(1)

        # close led on JY901
        self.i2c.write_i2c_block_data(0x50, 0x1b, [0x01, 0x00])
        # horizontally motieren
        self.i2c.write_i2c_block_data(0x50, 0x23, [0x00, 0x00])
        sleep(.5)
        # auto gyro calibration. [0x01,0x00] unauto.
        self.i2c.write_i2c_block_data(0x50, 0x63, [0x00, 0x00])
        sleep(.5)
        # begin calibration of acc
        self.i2c.write_i2c_block_data(0x50, 0x01, [0x01, 0x00])
        sleep(1)
        # # stop calibration of acc
        # self.i2c.write_i2c_block_data(0x50, 0x01, [0x00,0x00])
        # sleep(.5)
        # save change. [0x01,0x00] --> default
        self.i2c.write_i2c_block_data(0x50, 0x00, [0x00, 0x00])
        sleep(1)

        self.static_acc_error = array((0,0,0))
        getStaticError_thread = Thread(target=self.getStaticError, args=(), daemon=True)
        getStaticError_thread.start()

    def getLinearAcc(self):
        acc = array(self.get_acc())

        quaternion = array(self.get_quat())
        gravity_n = asarray([0, 0, 9.80665])
        rot_mat = self.quaternion_to_rotation_matrix(quaternion)
        gravity_b = dot(rot_mat, gravity_n)

        linear_acc = acc - gravity_b
        return linear_acc

    def get_acc(self):
        try:
            self.raw_acc_x = self.i2c.read_i2c_block_data(self.addr, 0x34, 2)
            self.raw_acc_y = self.i2c.read_i2c_block_data(self.addr, 0x35, 2)
            self.raw_acc_z = self.i2c.read_i2c_block_data(self.addr, 0x36, 2)
        except IOError as error:
            raise error
            return

        self.k_acc = 16 * 9.80665

        self.acc_x = (self.raw_acc_x[1] << 8 | self.raw_acc_x[0]) / 32768 * self.k_acc
        self.acc_y = (self.raw_acc_y[1] << 8 | self.raw_acc_y[0]) / 32768 * self.k_acc
        self.acc_z = (self.raw_acc_z[1] << 8 | self.raw_acc_z[0]) / 32768 * self.k_acc
        if self.acc_x >= self.k_acc:
            self.acc_x -= 2 * self.k_acc

        if self.acc_y >= self.k_acc:
            self.acc_y -= 2 * self.k_acc

        if self.acc_z >= self.k_acc:
            self.acc_z -= 2 * self.k_acc
        return (self.acc_x, self.acc_y, self.acc_z)

    def get_quat(self):
        try:
            self.raw_quat_0 = self.i2c.read_i2c_block_data(self.addr, 0x51, 2)
            self.raw_quat_1 = self.i2c.read_i2c_block_data(self.addr, 0x52, 2)
            self.raw_quat_2 = self.i2c.read_i2c_block_data(self.addr, 0x53, 2)
            self.raw_quat_3 = self.i2c.read_i2c_block_data(self.addr, 0x54, 2)
        except IOError as error:
            raise error
            return

        self.k_quat = 1

        self.quat_0 = (self.raw_quat_0[1] << 8 | self.raw_quat_0[0]) / 32768 * self.k_quat
        self.quat_1 = (self.raw_quat_1[1] << 8 | self.raw_quat_1[0]) / 32768 * self.k_quat
        self.quat_2 = (self.raw_quat_2[1] << 8 | self.raw_quat_2[0]) / 32768 * self.k_quat
        self.quat_3 = (self.raw_quat_3[1] << 8 | self.raw_quat_3[0]) / 32768 * self.k_quat
        if self.quat_0 >= self.k_quat:
            self.quat_0 -= 2 * self.k_quat

        if self.quat_1 >= self.k_quat:
            self.quat_1 -= 2 * self.k_quat

        if self.quat_2 >= self.k_quat:
            self.quat_2 -= 2 * self.k_quat

        if self.quat_3 >= self.k_quat:
            self.quat_3 -= 2 * self.k_quat

        return (self.quat_0, self.quat_1, self.quat_2, self.quat_3)

    def quaternion_to_rotation_matrix(self, quat):
        q = quat.copy()
        n = dot(q, q)
        if n < finfo(q.dtype).eps:
            return identity(4)
        q = q * sqrt(2.0 / n)
        q = outer(q, q)
        rot_matrix = array(
            [[1.0 - q[2, 2] - q[3, 3], q[1, 2] + q[3, 0], q[1, 3] - q[2, 0]],
             [q[1, 2] - q[3, 0], 1.0 - q[1, 1] - q[3, 3], q[2, 3] + q[1, 0]],
             [q[1, 3] + q[2, 0], q[2, 3] - q[1, 0], 1.0 - q[1, 1] - q[2, 2]]
             ],
            dtype=q.dtype)
        return rot_matrix

    def getStaticError(self):
        while True:
            try:
                linearAcc_group = self.getLinearAcc()
                time_prev = time()
                while time() - time_prev < .1:
                    linearAcc_group = row_stack((linearAcc_group, self.getLinearAcc()))
                    sleep(.008)
                    print
                linearAcc_group_var = var(linearAcc_group, axis=0, keepdims=True)
                #print (linearAcc_group_var)

                if linearAcc_group_var[0][0] < 1e-5 and linearAcc_group_var[0][1] < 1e-5 and linearAcc_group_var[0][2] < 1e-5:
                    self.static_acc_error = mean(linearAcc_group, axis=0, keepdims=True)[0]

            except:
                sleep(.001)
                continue


if __name__ == "__main__":
    bs = beschleunigungssensor()

    time_prev = time()
    while time() - time_prev < 100:
        accel_data = bs.getLinearAcc()
        print ('accel_data: ')
        print (accel_data)
        print ("static_acc_error: ")
        print (bs.static_acc_error)
        (accel_X, accel_Y, accel_Z) = accel_data - bs.static_acc_error
        print ("nach filten: ")
        print(format(accel_X, '.1f'), '  ', format(accel_Y, '.1f'), '  ', format(accel_Z, '.1f'))
        print ('\n\n\n')
        sleep(.2)
        
    '''
    while True:
        time_1 = time()
        all_druck = getAllPressure()
        #getallvarianz()
        print (all_druck)
        print (time()-time_1)
        sleep(.5)
    '''       
    '''
    while True:
        for i in range(1,6):
            print ('Thermocouple {0} Temperature: {1:0.3F}°C'.format(i, getTemperature(i)))
        print('\n')
        sleep(.3)
        #temp = getTemperature(5)
        #print(format(temp, '.1f'))'''

    '''
    accel_data = getAcceleration()
    accel_X = accel_data['x']
    accel_Y = accel_data['y']
    accel_Z = accel_data['z']
    print(accel_X)
    print(accel_Y)
    print(accel_Z)'''

# def getADC_Value(drucksensor_num):
#     # adc = ADS1115()
#     if drucksensor_num == 5:
#         addr = 0x49
#         drucksensor_num = 1
#     else:
#         addr = 0x48
#
#     adc = ADS1115(address=addr)
#     GAIN = 1
#     # adc.start_adc(drucksensor_num, gain=GAIN)
#     valueOfADC = adc.read_adc(drucksensor_num - 1, gain=GAIN)  # abs(adc.get_last_result())
#     # adc.stop_adc()
#     return valueOfADC
#
# def getSpg(drucksensor_num):
#     valueOfADC =  getADC_Value(drucksensor_num)
#     return (valueOfADC / 32767)*4.096

# def getAllPressure():
#     GAIN = 1
#
#     valueOfADC = [0]*5
#     volt =[0]*5
#     bar =[0]*5
#
#     for drucksensor_num in range(1, 6):
#         try:
#             if drucksensor_num == 5:
#                 addr = 0x49
#                 adc = ADS1115(address=addr)
#                 valueOfADC[drucksensor_num - 1] =  adc.read_adc(0, gain=GAIN)  #abs(adc.get_last_result())
#             else:
#                 addr = 0x48
#                 adc = ADS1115(address=addr)
#                 valueOfADC[drucksensor_num - 1] =  adc.read_adc(drucksensor_num - 1, gain=GAIN)  #abs(adc.get_last_result())
#             volt[drucksensor_num - 1] = round((valueOfADC[drucksensor_num - 1] / 32767)*4.096, 4)
#             #bar[drucksensor_num - 1] = round((10 / 3.3) * volt[drucksensor_num - 1], 4)            # 4-20mA entspricht 0-3.3V
#             #bar[drucksensor_num - 1] = round((125 / 33) * volt[drucksensor_num - 1] - 2.5, 2)      # 0-20mA entspricht 0-3.3V
#             bar[drucksensor_num - 1] = round((125 / 24) * volt[drucksensor_num - 1] - 2.5, 2)       # 0-25mA entspricht 0-3V
#             if bar[drucksensor_num - 1] < 0:
#                 bar[drucksensor_num - 1] = -1
#         except:
#             bar[drucksensor_num - 1] = -1
#     return bar

# def getallvalue():
#     GAIN = 1
#
#     valueOfADC = [0]*5
#     volt =[0]*5
#     bar =[0]*5
#
#     for drucksensor_num in range(1, 6):
#
#         if drucksensor_num == 5:
#             addr = 0x49
#             adc = ADS1115(address=addr)
#             valueOfADC[drucksensor_num - 1] =  adc.read_adc(0, gain=GAIN)  #abs(adc.get_last_result())
#         else:
#             addr = 0x48
#             adc = ADS1115(address=addr)
#             valueOfADC[drucksensor_num - 1] =  adc.read_adc(drucksensor_num - 1, gain=GAIN)  #abs(adc.get_last_result())
#         volt[drucksensor_num - 1] = round((valueOfADC[drucksensor_num - 1] / 32767)*4.096, 4)
#         #bar[drucksensor_num - 1] = round((10 / 3.3) * volt[drucksensor_num - 1], 4)            # 4-20mA entspricht 0-3.3V
#         #bar[drucksensor_num - 1] = round((125 / 33) * volt[drucksensor_num - 1] - 2.5, 2)      # 0-20mA entspricht 0-3.3V
#         bar[drucksensor_num - 1] = round((125 / 24) * volt[drucksensor_num - 1] - 2.5, 2)       # 0-25mA entspricht 0-3V
#
#     print('             | {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} |'.format(*range(1,6)))
#     print('-' * 58)
#     print('vlaue Of ADC:| {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} |'.format(*valueOfADC))
#
#     print('spannung:    | {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} |'.format(*volt))
#
#     print('bar:         | {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} |'.format(*bar))
#     print('\n')
#
# def detect_drucksensor(drucksensor_num):
#     valueOfADC = [0] * 100
#     for i in range(100):
#         valueOfADC[i] = getADC_Value(drucksensor_num)
#         sleep(0.01)
#
#     result = var(array(valueOfADC), ddof=1)
#     return result
#
# def getallvarianz():
#     varianz = [0]*5
#     for drucksensor_num in range(1, 6):
#         varianz[drucksensor_num - 1] = round(detect_drucksensor(drucksensor_num), 2)
#     print('             | {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} |'.format(*range(1,6)))
#     print('-' * 58)
#     print('varianz:     | {0:>6} | {1:>6} | {2:>6} | {3:>6} | {4:>6} |'.format(*varianz))
#     print('\n')


