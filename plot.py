import _tkinter
import os
import sys
import csv
import time
import shutil
import random
import numpy as np
import matplotlib.pyplot as plt

def saveData(data):
    local_path = os.path.split(os.path.realpath(__file__))[0]  # /home/pi/Luftdrucksensor_RPi
    # 识别数据的来源
    dataFrom = data[0]  # for example "1.slave_RPi_2"
    file_name = dataFrom[:11] + '.csv'

    # 将数据存入对应的csv文件
    try:
        with open(os.path.join(local_path, file_name), 'rb') as f:
            # 获得当前文本的行数，该信息被存放在了文本最后一行
            off = -50  # 设置偏移量
            while True:

                f.seek(off, 2)  # seek(off, 2)表示文件指针：从文件末尾(2)开始向前50个字符(-50)
                lines = f.readlines()  # 读取文件指针范围内所有行
                if len(lines) >= 2:  # 判断是否最后至少有两行，这样保证了最后一行是完整的
                    last_line = lines[-1]  # 取最后一行
                    
                    num_lines = int(last_line.decode().split(':')[1].lstrip())
                    
                    new_off = 0 - len(last_line)
                    break
                # 如果off为50时得到的readlines只有一行内容，那么不能保证最后一行是完整的
                # 所以off翻倍重新运行，直到readlines不止一行
                off *= 2
            # 删除最后一行
        with open(os.path.join(local_path, file_name), 'r+b') as f:
            
            f.seek(new_off, 2)
            f.truncate()
        # with open(os.path.join(local_path, file_name), 'r') as f:
        #     lines = f.readlines()
        #     for line in lines:
        #         print (line)
        
        # 在最后两行写入新的数据和总行数
        with open(os.path.join(local_path, file_name), 'a+', newline='') as f:
            file_writer = csv.writer(f)

            file_writer.writerow(data[1:])

            file_writer.writerow(["Number of lines: "+str(num_lines+1)])

        if num_lines == 7200:
            # 移动文件并改名字
            time_now = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
            new_file_name = dataFrom[:11]+ '-' + time_now[:-2] + '-1h'+ '.csv'

            new_path = 'pi/Desktop/Daten/' + os.listdir('pi/Desktop/Daten/')[-1]
            shutil.move(os.path.join(local_path, file_name), os.path.join(new_path, new_file_name))


    except FileNotFoundError:
        with open(os.path.join(local_path, file_name), 'a+', newline='') as f:
            file_writer = csv.writer(f)
            # file_writer.writerow(['Zeitpunkt des Empfangens', 'Drucksensor_1', 'Drucksensor_2', 'Drucksensor_3', 'Drucksensor_4',
            #                       'Drucksensor_5', 'Temperatursensor_1', 'Temperatursensor_1', 'Temperatursensor_1', 'Temperatursensor_1',
            #                       'Temperatursensor_1', 'Beschleunigung_X', 'Beschleunigung_Y', 'Beschleunigung_Z'])
            file_writer.writerow(data[1:])
            file_writer.writerow(["Number of lines: 1"])

    except IndexError:
        print (last_line.decode())


def readDataFrom(sender_id):
    for i in range(8):
        if sender_id >= (1 + 13 * i) and sender_id <= (13 + 13 * i):  # 1<=sender_id<=13, 14<=sender_id<=26......
            file_index = i + 1
    data_from_file = str(file_index) + '.slave_RPi.csv'  # for example: 1.salve_RPi.csv
    if sender_id % 13 == 0:
        data_from_col = 13  # 在数据文件中第一列（index对应是0）存放的是数据被收集的时间，第十四列的index对应13，但是13倍数对13取余是0.
    else:
        data_from_col = sender_id % 13

    return data_from_file, data_from_col

def getLastline(file_name):
    off = -50  # 设置偏移量

    with open(file_name, 'rb') as f:  # 打开大缓存文件

        while True:
            f.seek(off, 2)  # seek(off, 2)表示文件指针：从文件末尾(2)开始向前50个字符(-50)
            lines = f.readlines()  # 读取文件指针范围内所有行

            if len(lines) >= 3:  # 判断是否最后至少有两行，这样保证了最后2行是完整的

                last_line = lines[-1]  # 取最后一行

                if last_line[:6].decode() == "Number":
                    last_line = lines[-2]

                break
            # 如果off为50时得到的readlines只有一行内容，那么不能保证最后一行是完整的
            # 所以off翻倍重新运行，直到readlines不止一行
            off -= 50

    return last_line

def getDataFromLastline(last_line, data_from_col):
    return float(last_line.decode().split(',')[data_from_col])

def getDataFromLines(lines, data_from_col):
    result_y = []
    for line in lines:
        result_y .append(float(line.decode().split(',')[data_from_col]))

    return result_y

def getLines(file_name, lines_num):
    off = -50  # 设置偏移量
    num_inLast = False

    with open(file_name, 'rb') as f:  # 打开大缓存文件

        while True:
            f.seek(off, 2)  # seek(off, 2)表示文件指针：从文件末尾(2)开始向前50个字符(-50)
            lines = f.readlines()  # 读取文件指针范围内所有行

            if len(lines) >= 3:  # 判断是否最后至少有两行，这样保证了最后2行是完整的

                last_line = lines[-1]  # 取最后一行

                if last_line[:6].decode() == "Number":
                    num_inLast = True
                    lastline_len = len(last_line)
                    last2line_len = len(lines[-2])
                    new_off = 0 - (lastline_len + last2line_len * lines_num) - 50
                else:
                    lastline_len = len(last_line)

                    new_off = 0 - lastline_len * lines_num

                break
            # 如果off为50时得到的readlines只有一行内容，那么不能保证最后一行是完整的
            # 所以off翻倍重新运行，直到readlines不止一行
            off -= 50

        while True:
            f.seek(new_off, 2)

            lines = f.readlines()

            if num_inLast:
                if len(lines) == lines_num+1:
                    lines = lines[:-1]
                    break

                elif len(lines) < lines_num+1:
                    new_off -= 50

                else:
                    new_off += 50

            else:
                if len(lines) == lines_num:
                    lines = lines[:]
                    break

                elif len(lines) < lines_num:
                    new_off -= 50
                else:
                    new_off += 50

    return lines

def plot_init(plt, data_from_file, data_from_col, x, y):
    plt.xlabel('Time/s')
    if data_from_col >= 1 and data_from_col <= 5:
        plt.title('Drucksensor')
        plt.ylabel('Pressure/bar')
        lab = str(data_from_col) + "DS"
    elif data_from_col >= 6 and data_from_col <= 10:
        plt.title('Temperatursensor')
        plt.ylabel('Temperature/°C')
        lab = str(data_from_col-5) + "TS"
    elif data_from_col == 11:
        plt.title('Beschleunigungssensor')
        plt.ylabel('Acceleration/m/s-2')
        lab = "BS_X"
    elif data_from_col == 12:
        plt.title('Beschleunigungssensor')
        plt.ylabel('Acceleration/m/s-2')
        lab = "BS_Y"
    else:
        plt.title('Beschleunigungssensor')
        plt.ylabel('Acceleration/m/s-2')
        lab = "BS_Z"

    lab = str(data_from_file[0]) + ".slave_RPi_" + lab
    plt.plot(x, y, color='red', label=lab)
    plt.legend()


def plot_dynamic(data_from_file, data_from_col):
    plt.ion()  ## Note this correction #打开交互模式
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    i = 0
    x = list()
    y = list()

    plot_init(plt, data_from_file, data_from_col, x, y)

    time_1 = time.time()

    try:
        while i < 7200:     # one hour

            time_2 = time.time()
            if time_2 - time_1 >= 0.5:      # 每0.5秒读取并更新一次最新数据
                time_1 = time_2

                new_y = getDataFromLastline(getLastline(data_from_file), data_from_col)
                x.append(i)
                y.append(new_y)
                ax.clear()  #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
                ax.plot(x, y,color='red')

                i += 0.5
                seconds_lim = 10
                ax.set_xlim(left=max(0, i - seconds_lim), right=i)       # one minute
                plt.text(x[-1], y[-1], y[-1], fontsize=8)
                plt.show()

                plt.pause(0.45)  # Note this correction

            plt.pause(0.0001)  # Note this correction


    except:
        try:
            plt.clf()  # 清除图像
            plt.close()  # 关闭图像
        except:
            plt.clf()  # 清除图像
            plt.close()  # 关闭图像
        finally:
            plt.clf()  # 清除图像
            plt.close()  # 关闭图像

    finally:
        plt.clf()  # 清除图像
        plt.close()  # 关闭图像

def handle_close(evt):
    global ax
    lines = getLines('1.slave_RPi.csv', 20 + 1)
    x1 = np.linspace(0, 10, 20 + 1)
    y1 = getDataFromLines(lines, 1+1)
    ax.plot(x1, y1, color='green')
    plt.show()
    #print (111111)

def plot_static(data_from_file, data_from_col, minutes):
    global ax
    # 初始化图板
    fig, ax = plt.subplots()
    fig.canvas.mpl_connect('button_press_event', handle_close)

    # 生成数据
    seconds = int(minutes * 60)
    lines_num = seconds * 2
    lines = getLines(data_from_file, lines_num+1)
    x = np.linspace(0, seconds, lines_num + 1)
    y = getDataFromLines(lines, data_from_col)

    # 画图
    ax.plot(x, y, color = 'red')
    plot_init(plt, data_from_file, data_from_col, x, y)

    # 标注数据在图中
    x_text = []
    y_text = []
    text_num = 10
    for i in range(0, lines_num+1, int(lines_num/text_num)):
        x_text.append(x[i])
        y_text.append(y[i])

    for i, j in zip(x_text, y_text):
        plt.text(i, j, j, fontsize=8)


    plt.show()


if __name__ == "__main__":
    #plot_dynamic("1.slave_RPi.csv", 11)
    plot_static("1.slave_RPi.csv", 12, 1/6)

