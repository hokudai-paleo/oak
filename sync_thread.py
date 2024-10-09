from PyQt5.QtCore import QThread
import PyQt5.QtCore
import time
import os

import subprocess
import glob
from pathlib import Path


ISEND_BASENAME = "isend.txt"
EXCLUDE_SEI_BASENAME = "exclude_files_sei.txt"
EXCLUDE_HUKU_BASENAME = "exclude_files_huku.txt"

ALERT_PATH = os.path.join(os.getcwd(),"lto_change.txt")

class SyncThread(QThread):
    printThread = PyQt5.QtCore.pyqtSignal(str)
    printThread2 = PyQt5.QtCore.pyqtSignal(str)
    def run(self):
        
        self.printThread.emit("[SYNC MODE START]")

        self.isARW = self.ui.cb_write_arw.isChecked()
        self.isTIF = self.ui.cb_write_tif.isChecked()
        self.isAnimation = self.ui.cb_write_animation.isChecked()
        self.isLabBook = self.ui.cb_write_lab.isChecked()
        self.isMetadata = self.ui.cb_write_meta.isChecked()

        self.OUTPUT_PATH = self.ui.l_output_volume.text()
        self.LTO_SEI_PATH = self.ui.l_output_volume_sei.text()
        self.LTO_HUKU_PATH = self.ui.l_output_volume_huku.text()

        self.CHECKSUM_TMP_PATH = os.path.join(self.OUTPUT_PATH,'checksum_tmp.txt')
        self.CHECKSUM_ALL_SEI_PATH = os.path.join(self.OUTPUT_PATH,'checksum_all_sei.txt')
        self.CHECKSUM_ALL_HUKU_PATH = os.path.join(self.OUTPUT_PATH,'checksum_all_huku.txt')

        
        if(self.ARW_NUMBER == 1):
            self.ARW_NUMBER = 0
        
        exclude_files_txt_path = os.path.join(os.getcwd() ,"sync_settings",EXCLUDE_SEI_BASENAME)
        f = open(exclude_files_txt_path,"w")
        f.close()
        f = open(self.CHECKSUM_ALL_SEI_PATH,'w')
        f.close()

        if(self.rb_lto_opt == "Both"):
            exclude_files_txt_path = os.path.join(os.getcwd() ,"sync_settings",EXCLUDE_HUKU_BASENAME)
            f = open(exclude_files_txt_path,"w")
            f.close()
            f = open(self.CHECKSUM_ALL_HUKU_PATH,'w')
            f.close()

        self.printThread.emit("    [INFO]Config file created")

        while True:
            self.main_loop()
            if("[MESSAGE]Synching" in self.ui.textBrowser.toPlainText()):
                self.printThread.emit('------------------------------------------')
                self.printThread.emit("    [INFO]TIF convered")
                self.printThread.emit("    [INFO]Synching")
                self.main_loop(True)
                self.printThread.emit("[SYNC MODE END]")
                exit()

    def main_loop(self,final_flag = False):

        TARGETS_PATHS = [f.path for f in os.scandir(self.OUTPUT_PATH) if f.is_dir()]
        TARGETS_PATHS = [x for x in TARGETS_PATHS if not 'Lab_book' in x]
        TARGETS_PATHS.sort()
        
        for lto_send_path in TARGETS_PATHS:
            if(self.isARW):
                self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Rawdata_PSMS_" + str(self.ARW_NUMBER)),True)
                if(self.rb_lto_opt == "Both"):
                    self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Rawdata_PSMS_" + str(self.ARW_NUMBER)),False)

            if(self.isTIF):
                self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Images"),True)
                if(self.rb_lto_opt == "Both"):
                    self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Images"),False)
    
            if(final_flag == True):
                if(self.isAnimation) and (self.SAME_TIME_MODE == False):
                    self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Animation"),True)
                    if(self.rb_lto_opt == "Both"):
                        self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Animation"),False)

                if(self.isMetadata):
                    self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Metadata"),True)
                    if(self.rb_lto_opt == "Both"):
                        self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , os.path.basename(lto_send_path), "Metadata"),False)
                
                if(self.isLabBook):
                    self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , "Lab_book"),True)
                    if(self.rb_lto_opt == "Both"):
                        self.target_files(os.path.join(os.path.basename(self.OUTPUT_PATH) , "Lab_book"),False)

        time.sleep(3)
    
    def target_files(self,common_path,issei):
        if(issei == True):
            exclude_files_txt_path = os.path.join(os.getcwd() ,"sync_settings",EXCLUDE_SEI_BASENAME)
            LTO_PATH = self.LTO_SEI_PATH
            CHECKSUM_ALL_PATH = self.CHECKSUM_ALL_SEI_PATH
            
        else:
            exclude_files_txt_path = os.path.join(os.getcwd() ,"sync_settings",EXCLUDE_HUKU_BASENAME)
            LTO_PATH = self.LTO_HUKU_PATH
            CHECKSUM_ALL_PATH = self.CHECKSUM_ALL_HUKU_PATH
        exclude_files_path = []

        #mkdir
        lto_send_path = os.path.join(LTO_PATH , common_path)
        
        if not os.path.exists(lto_send_path):# 無ければ
            os.makedirs(lto_send_path)

        with open(exclude_files_txt_path) as f:
            for line in f:
                exclude_files_path.append(line.replace("\n",""))

        from_path = os.path.join(Path(self.OUTPUT_PATH).parent,common_path)
        
        from_all_files_path = glob.glob(os.path.join(from_path,"*"))
        send_files_paths = list(set(from_all_files_path) - set(exclude_files_path))

        send_files_paths.sort()

        if(len(send_files_paths) != 0):
            self.printThread.emit('------------------------------------------')
            if(issei == True) and ("Rawdata_PSMS_" in common_path):  
                self.printThread.emit("    [INFO]Synching ARW (Primary)")
            elif(issei == True) and ("Images" in common_path):  
                self.printThread.emit("    [INFO]Synching TIF (Primary)")
            elif(issei == False) and ("Rawdata_PSMS_" in common_path):  
                self.printThread.emit("    [INFO]Synching ARW (Duplicate)")
            elif(issei == False) and ("Images" in common_path):  
                self.printThread.emit("    [INFO]Synching (Duplicate)")
            elif(issei == True) and ("Animation" in common_path):  
                self.printThread.emit("    [INFO]Synching Animation (Primary)")
            elif(issei == True) and ("Metadata" in common_path):  
                self.printThread.emit("    [INFO]Synching Metadata (Primary)")
            elif(issei == False) and ("Animation" in common_path):  
                self.printThread.emit("    [INFO]Synching Animation (Duplicate)")
            elif(issei == False) and ("Metadata" in common_path):  
                self.printThread.emit("    [INFO]Synching Metadata (Duplicate)")
            elif(issei == True) and ("Lab_book" in common_path):  
                self.printThread.emit("    [INFO]Synching Lab Book (Primary)")
            elif(issei == False) and ("Lab_book" in common_path):  
                self.printThread.emit("    [INFO]Synching Lab Book (Duplicate)")

        send_total_size = 0
        for file in send_files_paths:
            send_total_size = send_total_size + os.path.getsize(file)
        mb_size_unit,mb_send_total_size = convert_size(send_total_size,"MB")
        
        cmd=["df","-m",LTO_PATH]
        result = subprocess.run(cmd,capture_output=True, text=True).stdout.splitlines()
        result=result[1].split(' ')
        result = [a for a in result if a != '']
        
        mb_nokori = int(result[3])

        if(mb_nokori - mb_send_total_size > 0):
            
            self.copy_verify(send_files_paths,LTO_PATH,CHECKSUM_ALL_PATH,exclude_files_txt_path,lto_send_path,mb_nokori,mb_send_total_size)
        
        else:
            self.change_lto_tape(issei)

        time.sleep(3)
        
    def copy_verify(self,send_files_paths,LTO_PATH,CHECKSUM_ALL_PATH,exclude_files_txt_path,lto_send_path,mb_nokori,mb_send_total_size):
        
        if(len(send_files_paths) == 0):
            pass
        else:
            self.printThread.emit("    [INFO]LTO free space: " + str(mb_nokori) + "MB")
            self.printThread.emit("    [INFO]Data size :" + str(mb_send_total_size) + "MB")
            cmd_md5 = ['md5sum']
            self.printThread.emit("    [INFO]Copying")
            file_counter = 1
            for from_file in send_files_paths:
                to_file = os.path.join(lto_send_path,os.path.basename(from_file))

                cmd = ["cp",from_file,to_file]
                self.printThread.emit("     [INFO](" + str(file_counter) + "/" + str(len(send_files_paths)) + ")  " + str(from_file))
                result = subprocess.check_output(cmd)

                cmd_md5.append(str(os.path.join(from_file,to_file)))
                file_counter = file_counter + 1
            
            result = subprocess.check_output(cmd_md5)
            result = result.decode('sjis')
            f = open(self.CHECKSUM_TMP_PATH,'w')
            f.write(result.replace(self.OUTPUT_PATH, LTO_PATH))
            f.close()

            f = open(CHECKSUM_ALL_PATH,'a')
            f.write(result)
            f.close()
            self.printThread.emit("    [INFO]Config file generated")
            
            cmd = ["md5sum", "--check", self.CHECKSUM_TMP_PATH]
            self.printThread.emit("    [INFO]Verifying")
            result = subprocess.run(cmd,capture_output=True, text=True).stdout
            self.printThread.emit(result)

            if("FAILED" in result):
                f = open(CHECKSUM_ALL_PATH,'a')
                f.write("Checksum Error:" + result[i] + '\n')
                f.close()
                self.printThread.emit("    [ERROR!!!]An error occurred at verifying. Check " + str(CHECKSUM_ALL_PATH) + " ")
            else:
                f = open(exclude_files_txt_path,'a')
                for i in range(len(send_files_paths)):
                    f.write(send_files_paths[i] + '\n')
                f.close()
                self.printThread.emit("    [INFO]Verify completed")

    def change_lto_tape(self,issei):
        self.printThread.emit('------------------------------------------')
        if(issei == True):
            LTO_PATH = self.LTO_SEI_PATH
            target_button = self.ui.b_output_volume_sei_change
            target_label = self.ui.l_output_volume_sei
            if(self.ui.rb_lto_dev_num_sei_0.isChecked() == True):
                lto_dev_number = 0
            else:
                lto_dev_number = 1
            self.printThread.emit("    [ERROR!!!]Out of LTO free space (Primary)")
            
        else:
            LTO_PATH = self.LTO_HUKU_PATH
            target_button = self.ui.b_output_volume_huku_change
            target_label = self.ui.l_output_volume_huku
            if(self.ui.rb_lto_dev_num_sei_0.isChecked() == True):
                lto_dev_number = 1
            else:
                lto_dev_number = 0
            self.printThread.emit("    [ERROR!!!]Out of LTO free space (Duplicate)")

        target_label.setText("Change")
        #アンマウントコマンド
        cmd=["sudo","umount", str(LTO_PATH)]
        subprocess.run(cmd)
        self.printThread.emit("    [INFO]" + str(LTO_PATH) + ' unmounted')

        time.sleep(5)
        self.printThread.emit("    [MESSAGE]Change " + str(LTO_PATH) + " and push button")
        target_button.setDisabled(False)

        while(True):#交換待ち
            #交換中loop
            time.sleep(3)
            if(target_label.text() == ("OK")):#交換完了ボタン押下
                #フォーマット
                target_button.setDisabled(True)
                self.printThread.emit("    [INFO]Formatting " + str(LTO_PATH) + "")
                cmd=["mkltfs","-d", str(lto_dev_number),"-f"]
                result = subprocess.check_output(cmd)
                self.printThread.emit("        formatted")
                
                #マウントコマンド
                self.printThread.emit("    [INFO]Mounting " + str(LTO_PATH) + " ")
                cmd = ["sudo","ltfs",LTO_PATH,"-o","devname=" + str(lto_dev_number)]
                result = subprocess.check_output(cmd)
                self.printThread.emit("    [INFO]Mounted")

                target_button.setDisabled(True)
                target_label.setText(str(LTO_PATH))
                
                self.printThread.emit("    [INFO]" + str(LTO_PATH) + " changed")
                self.printThread.emit("    [INFO]Back to resumed process after 5 sec.")
                self.printThread.emit('------------------------------------------')
                time.sleep(5)
                break


def convert_size(size, unit="B"):
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB")
    i = units.index(unit.upper())
    size = round(size / 1024 ** i, 2)

    return f"{size} {units[i]}",size

