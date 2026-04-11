import psutil

import datetime

#1.CPU方面
print("\nCPU方面")
#cpu_times():统计CPU时间
#输出格式：命名元组（ntuple），包含以下字段：
#user：用户模式下的CPU时间（秒）
#nice：低优先级用户模式下的CPU时间（秒）
#system：系统模式下的CPU时间（秒）
#idle：空闲时间（秒）
#iowait：等待I/O完成的时间（秒）
#irq：硬件中断时间（秒）
#softirq：软件中断时间（秒）
#steal：被其他虚拟机占用的时间（秒）
#guest：运行虚拟机的用户模式下的CPU时间（秒）
#guest_nice：运行低优先级虚拟机的用户模式下的CPU时间（秒）
cpu_times = psutil.cpu_times()

#cpu_percent():统计CPU使用率
#输出格式：float类型，范围0-100或者list（若percpu=True）
#注意：interval参数表示统计时间间隔，单位为秒。若不指定，则默认使用1秒。所以其=1是必须的，否则会返回0
cpu_percent = psutil.cpu_percent(interval=1,percpu=True)

#2.内存方面
print("\n内存方面")
#virtual_memory():统计内存信息
#输出格式：命名元组（ntuple），包含以下字段：
#total：总内存（字节）
#available：可用内存（字节）
#percent：内存使用率（%）
#used：已用内存（字节）
#free：空闲内存（字节）
#active：活动内存（字节）
#inactive：非活动内存（字节）
#buffers：缓存内存（字节）
#cached：缓存内存（字节）
#shared：共享内存（字节）
#slab： slab分配器内存（字节）
mem = psutil.virtual_memory()
print(f"Shared (Linux): {getattr(mem, 'shared', 0) / (1024**3):.2f} GB")#共享内存（GB）
#3.磁盘方面
print("\n磁盘方面")
#disk_usage():统计磁盘使用情况
#输出格式：命名元组（ntuple），包含以下字段：
#total：总磁盘空间（字节）
#used：已用磁盘空间（字节）
#free：空闲磁盘空间（字节）
#percent：磁盘使用率（%）
disk_usage = psutil.disk_usage('/')
print(f"Root Partition Usage:{disk_usage.percent}%")

#disk_io_counters():统计磁盘I/O信息
#输出格式：命名元组（ntuple），包含以下字段：
#read_count：读取操作次数
#write_count：写入操作次数
#read_bytes：读取字节数
#write_bytes：写入字节数
#read_time：读取时间（毫秒）
#write_time：写入时间（毫秒）
disk_io = psutil.disk_io_counters()
#4.网络方面
print("\n网络方面")
#net_io_counters():统计网络I/O信息
#输出格式：命名元组（ntuple），包含以下字段：
#bytes_sent：发送的字节数
#bytes_recv：接收的字节数
#packets_sent：发送的包数
#packets_recv：接收的包数
#errin：接收错误数
#outerr：发送错误数
net_io = psutil.net_io_counters()