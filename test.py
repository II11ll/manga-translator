import subprocess
command = 'cd comic-text-detector && python inference.py'
result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, text=True)
print(result.stdout)