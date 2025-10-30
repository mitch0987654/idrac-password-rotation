from paramiko import SSHClient, AutoAddPolicy
import random
import string
from keepercommander.__main__ import get_params_from_config
from keepercommander.commands.record_edit import RecordUpdateCommand
from keepercommander import api

keeperParams = get_params_from_config("config.json")
api.login(keeperParams)
api.sync_down(keeperParams)

def generateRandomPassword(length):
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL_CHARS = "!@#$%^&*()-_+="
    all_chars = LOWERCASE + UPPERCASE + DIGITS + SPECIAL_CHARS
    secure_string = [
        random.choice(LOWERCASE),
        random.choice(UPPERCASE),
        random.choice(DIGITS),
        random.choice(SPECIAL_CHARS)
    ]
    remaining_length = length - len(secure_string) 
    for _ in range(remaining_length):
        secure_string.append(random.choice(all_chars))
    random.shuffle(secure_string)
    return "".join(secure_string)

def updateKeeperRecord(idracIP, passwordstr):
    record_search = api.search_records(keeperParams, idracIP)
    for record in record_search:
        if (idracIP == record.notes):
            print("found 1 keeper record matching search parameters: " + idracIP)
            print("Updating keeper record password to: " + passwordstr)
            RecordUpdateCommand().execute(keeperParams, record=record.record_uid, fields=['password=' + passwordstr])   

def getKeeperPasswordForRouter(idracIP):
    record_search = api.search_records(keeperParams, idracIP)
    for record in record_search:
        if (idracIP == record.notes):
            return ("" + record.password)
            #print("title:" + record.title, ", password:" + record.password, ", notes:" + record.notes)

# List of iDRAC IPs
idrac_hosts = [
    "192.168.1.1",
    "192.168.1.2",
    "192.168.1.3",
]

for host in idrac_hosts:
    print(f"Updating idrac password on {host}...")
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    try:
        currentpassword = getKeeperPasswordForRouter(host)
        ssh.connect(hostname=host, username="root", password=currentpassword, timeout=10)

        newpassword = generateRandomPassword(45)
        cmd = f"racadm set iDRAC.Users.2.Password {newpassword}"
        print(cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)

        print(stdout.read().decode().strip())
        err = stderr.read().decode().strip()
        if err:
            print(f"Error on {host}: {err}")
        else:
            print(f"Password updated successfully on {host}")
            updateKeeperRecord(host,newpassword)
    except Exception as e:
        print(f"Failed to update {host}: {e}")
    finally:
        ssh.close()

