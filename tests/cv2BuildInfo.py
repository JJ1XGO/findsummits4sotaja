import cv2

print(cv2.getBuildInformation())
print(f"cv2.getNumberOfCPUs():{cv2.getNumberOfCPUs()}")
print(f"cv2.getNumThreads():{cv2.getNumThreads()}")
print(f"cv2.useOptimized():{cv2.useOptimized()}")
print("")
#
print("--following is OpenCL info--")
device = cv2.ocl.Device_getDefault()
print(f"available: {device.available()}")
print(f"Version: {device.version()}")
print(f"OpenCL Version: {device.OpenCLVersion()}")
print(f"Driver version: {device.driverVersion()}")
#
print(f"Vendor ID: {device.vendorID()}")
print(f"Vendor name: {device.vendorName()}")
print(f"Name: {device.name()}")
print(f"Device Version Major: {device.deviceVersionMajor()}")
print(f"Device Version Minor: {device.deviceVersionMinor()}")
#
print( f"Is a NVidia device: {device.isNVidia()}")
print( f"Is an AMD device: {device.isAMD()}")
print( f"Is a Intel device: {device.isIntel()}")
#
print(f"Max Clock Frequency: {device.maxClockFrequency()}")
print(f"Max Compute Units: {device.maxComputeUnits()}")
print(f"Max Memory Alloc Size: {device.maxMemAllocSize()}")
print(f"Global Memory size: {device.globalMemSize()}")
print(f"Memory cache size: {device.globalMemCacheSize()}")
print(f"Memory cache type: {device.globalMemCacheType()}")
print(f"Local Memory size: {device.localMemSize()}")
print(f"Local Memory type: {device.localMemType()}")
#
