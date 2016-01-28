import os, shutil, re, errno, zipfile, time
from os import listdir, walk
from os.path import isfile, join

new_version = ''

def UpdateBuild(file):
	global new_version
	f = open(file, 'r')
	data = f.read()
	f.close()
	m = re.compile('version="(.*?)" provider-name').findall(data)
	if len(m) > 0:
		old_version = m[0]
		v = old_version.split('.')
		old_build = v[2]
		new_build = int(old_build) + 1
		new_version = "%s.%s.%s" % (v[0], v[1], new_build)
		new_content = data.replace('version="%s" provider-name' % old_version, 'version="%s" provider-name' % new_version)
		f = open(file, 'w')
		f.write(new_content)
		f.close()
		output.write( " build %s incremented to %s" % (old_build, new_build))
	return new_version

def AddChangeLog(file):
	f = open(file, 'a')
	new_data = '\n[B]*** %s ***[/B]' % new_version
	f.write(new_data)
	new_data = '\n- '
	f.write(new_data)
	f.close()
	
dir = os.getcwd()
pluginName = dir.split("\\")[-1]
dir = os.path.join(dir, pluginName)
kodidir = os.path.join(os.environ['APPDATA'], r"Kodi\addons", pluginName)
addonFiles = []

output = open("build_output.txt", "w")
output.write( "ADDON: " + pluginName + " by HarryGG")
output.write( "\n---------------")
output.write( "\nGITHUB DIR:\n")
output.write( dir )
output.write( "\nKODI DIR:\n")
output.write( kodidir )
output.write(  "\nFILES:")

for src_dir, subdirs, files in os.walk(kodidir):
	dst_dir = src_dir.replace(kodidir, dir, 1)
	if not os.path.exists(dst_dir):
		os.mkdir(dst_dir)
		
	for file_ in files:
		if 'pyo' not in file_:
			src_file = os.path.join(src_dir, file_)
			dst_file = os.path.join(dst_dir, file_)
			f = pluginName + dst_file.replace(dir, "")
			output.write(  "\n.\\" + f)
			addonFiles.append(f)
			if os.path.exists(dst_file):
				os.remove(dst_file)
			shutil.copy(src_file, dst_dir)
			#remove debugging
			if 'py' in dst_file and '__init__' not in dst_file:
				f = open(dst_file, 'r')
				data = f.read()
				f.close()
				m = re.compile('(#append_pydev_remote_debugger.*?#end_append_pydev_remote_debugger)', re.DOTALL).findall(data)
				if len(m) > 0:
					output.write( " * found and removed debug lines")
					new_content = data.replace(m[0], '')
					f = open(dst_file, 'w')
					f.write(new_content)
					f.close()
			#Update build number
			if 'addon.xml' in dst_file:
				UpdateBuild(dst_file)
			#Update changelog
			if 'changelog.txt' in dst_file:
				AddChangeLog(dst_file)

output.write( "\n--------------")
output.write( "\nTOTAL: %s files " % len(addonFiles) )

#Zip file
zipFileName = pluginName + ".zip"
if os.path.exists(zipFileName):
	os.remove(zipFileName)
zf = zipfile.ZipFile(zipFileName, "w")
for dirname, subdirs, files in os.walk(pluginName):
	zf.write(dirname)
	for filename in files:
		zf.write(os.path.join(dirname, filename))
zf.close()

output.write( "\nZIP FILE: "  + zipFileName)
output.write( "\nVERSION: "  + new_version)
localtime = time.asctime( time.localtime(time.time()) )
output.write ("\nBUILD TIME: " + localtime)
output.close()

#Print output
f = open("build_output.txt", 'r')
data = f.read()
f.close()
print data



