from genericpath import isfile
from tkinter import SEL_FIRST
from PyQt5.QtCore import QThread
import PyQt5.QtCore
import os
import re
import shutil
import subprocess
import requests
import glob
import time
import webbrowser
import numpy as np
from mpi4py import MPI
from pathlib import Path
import datetime

from create_logs import CreateLog
import create_logs
import edit_slide

comm = MPI.COMM_WORLD

ARW_COMBINATION_NUMBER = 16

KAKIKOMI_TIME = 2

MAX_TIF_NUM = 1000

class ActionThread(QThread):
    
    printThread = PyQt5.QtCore.pyqtSignal(str)
    def run(self):
        #照明の数(1~4)
        self.LIGHT_TYPE_NUM = len(self.light_type_names)
        self.SAMETIME_MODE = self.ui.cb_same_time_mode.isChecked()
        
        self.movie_names = []
        self.light_dirs = []
        self.caption_names = []

        self.tif_counter = 0

        #ピクセルシフト値からARWの枚数を設定する。
        global ARW_COMBINATION_NUMBER
        if(self.pixel_shift == "PSMS16"):
            ARW_COMBINATION_NUMBER = 16
        elif(self.pixel_shift == "PSMS4"):
            ARW_COMBINATION_NUMBER = 4
        else: #self.ui.comb_pixel_shift_nulti_shooting.currentText() == "not"
            ARW_COMBINATION_NUMBER = 1
    
        #カメラのフレーム値の変更フラグ
        self.frame_change = False
        if("GFX 100s" in self.camera_name):
            self.frame_change = True
        
        self.INPUT_VOLUME = self.input_volumes[0].text()

        

        #OUTPUT_VOLUME(INPUT,TMP,OUTPUT)の作成先選択
        if(self.ui.l_output_volume.text() == "not selected") and (self.ui.l_tmp_volume.text() == "not selected"):
            self.OUTPUT_VOLUME = self.INPUT_VOLUME
        elif(self.ui.l_tmp_volume.text() != "not selected") and (self.ui.l_output_volume.text() == "not selected"):
            self.OUTPUT_VOLUME = self.ui.l_tmp_volume.text()
        else:
            self.OUTPUT_VOLUME = self.ui.l_output_volume.text()

        #TMP_VOLUME(INPUT,TMP,OUTPUT)の作成先選択
        if(self.ui.l_tmp_volume.text() != "not selected"):
            self.TMP_VOLUME = self.ui.l_tmp_volume.text()
        elif(self.ui.l_output_volume.text() != "not selected"):
            self.TMP_VOLUME = self.ui.l_output_volume.text()
        else:
            self.TMP_VOLUME = self.INPUT_VOLUME

        #照明の数(1~4)だけディレクトリを作る
        for i in range(self.LIGHT_TYPE_NUM):
            #親フォルダ(デジタル標本番号-照明種類-…-NNNN)作成
            if(self.SAMETIME_MODE == True):
                dist_dir = self.OUTPUT_VOLUME + '/' + self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i]+ '_' + self.positions[i] + "_" + str(1).zfill(4) + '-NNNN'
            else:
                dist_dir = self.OUTPUT_VOLUME + '/' + self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i]+ '_' + self.positions[i] + "_" + str(1).zfill(4) + '-' + str(self.picture_nums).zfill(4)


            if(self.SAMETIME_MODE == True):
                metadata_path = dist_dir + '/Metadata/' +  self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i]+ '_' + self.positions[i] + "_" + str(1).zfill(4) + '-NNNN' + "_metadata.xlsx"
            else:
                metadata_path = dist_dir + '/Metadata/' +  self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i]+ '_' + self.positions[i] + "_" + str(1).zfill(4) + '-' + str(self.picture_nums).zfill(4) + "_metadata.xlsx"

            if(self.SAMETIME_MODE == True):
                meta_name = self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i]+ '_' + self.positions[i] + "_" + str(1).zfill(4) + '-NNNN'
            else:
                meta_name = self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i]+ '_' + self.positions[i] + "_" + str(1).zfill(4) + '-' + str(self.picture_nums).zfill(4)
            
            if self.voxel_pare[i]:
                pass
            else:
                self.voxel_pare[i] = ""

            self.create_dir_log(dist_dir,metadata_path,self.light_type_names[i],self.temperature_pare[i],self.voxel_pare[i],meta_name,self.grinding_tools)
            self.light_dirs.append(dist_dir)

            #Readmeをコピーする
            dist_path_1 = os.path.join(os.getcwd() , 'template/readme.txt')
            if(ARW_COMBINATION_NUMBER == 1):
                dist_path_2 = os.path.join(dist_dir , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER - 1),'readme.txt')
            else:
                dist_path_2 = os.path.join(dist_dir , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER),'readme.txt')
            shutil.copyfile(dist_path_1,dist_path_2)

            if(self.SAMETIME_MODE == False):
                movie_name = os.path.join(dist_dir , 'Animation' , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i] + '_' + self.positions[i] + "_" + str(1).zfill(4) + '-' + str(self.picture_nums).zfill(4) + '_animation.mov')
            else:
                movie_name = os.path.join(dist_dir , 'Animation' , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[i] + '_' + self.positions[i] + "_" + str(1).zfill(4) + '-NNNN_animation.mov')
            
            self.movie_names.append(movie_name)
            
        
            #create caption
            caption_name = edit_slide.create_caption(self.taxon_lithology,self.ui.e_geological_age.text(),self.ui.e_locality.text(),self.ui.e_digital_specimen_number.text(),self.OUTPUT_VOLUME +"/tmp",self.light_type_names[i],str(1).zfill(4) + "-" + str(self.picture_nums).zfill(4),movie_name,self.ui.e_horizon.text(),self.ui.e_pixel_width.text(),self.ui.voxels[0],str(self.ui.e_major_axis.text()) + "x" + str(self.ui.e_minor_axis.text()),self.ui.e_fov.text(),self.positions[i],self.frame_change,self.ui.e_taxon_lithology.text(),self.ui.cb_shatai.isChecked(),self.camera_name,self.SAMETIME_MODE)
            
            self.caption_names.append(caption_name)
            
        if(self.ui.cw_movie.isChecked() == True):
            self.chat_message_send("Caption output")

        dist = self.main_loop()

        if(self.rb_lto_opt != "No"):
            self.printThread.emit("[MESSAGE]Sync...")
            while True:
                time.sleep(3)
                if("SYNC MODE END" in self.ui.tb_sync.toPlainText()):
                    break

        if(self.SAMETIME_MODE):
            self.replace_mode()
        
        self.remove_files_from_input()
        self.printThread.emit("[APP END]")

        if(self.ui.cw_end.isChecked() == True):
            self.chat_message_send("App end")
        print('------------------------------------------')
        print("app end")
        

    def replace_mode(self):

        self.printThread.emit("[REPLACE MODE START]")
        tif_number_str = str(int(self.tif_counter/len(self.light_dirs))).zfill(4)
        
        #Animationキャプション,Metadata差し替え
        for i in range(len(self.caption_names)):
            
            self.printThread.emit("    [INFO]Caption replaced")
            #cut
            command = 'ffmpeg -loglevel quiet -ss 2 -i ' + self.caption_names[i] + ' -c copy ' + self.light_dirs[i] + '/nocaption.mov'
            subprocess.call(command, shell=True)

            #new caption
            caption_name = edit_slide.create_caption(self.taxon_lithology,self.ui.e_geological_age.text(),self.ui.e_locality.text(),self.ui.e_digital_specimen_number.text(),self.OUTPUT_VOLUME + "/tmp",self.light_type_names[i],str(1).zfill(4) + "-" + tif_number_str,self.caption_names[i],self.ui.e_horizon.text(),self.ui.e_pixel_width.text(),self.ui.voxels[i],str(self.ui.e_major_axis.text()) + "x" + str(self.ui.e_minor_axis.text()),self.ui.e_fov.text(),self.positions[i],self.frame_change,self.ui.e_taxon_lithology.text(),self.ui.cb_shatai.isChecked(),self.camera_name,False)
            command = 'ffmpeg -loglevel quiet -i ' + self.caption_names[i] + ' -i ' + self.light_dirs[i] + '/nocaption.mov -vcodec mjpeg -pix_fmt yuv420p -b:v 600000000000000 -r 15 -filter_complex concat ' + self.light_dirs[i] + "/result.mov"
            subprocess.call(command,shell=True)
            
            time.sleep(2)
            self.printThread.emit("    [INFO]Created new caption " + str(i + 1) + "/" + str(len(self.caption_names)))
            
            # 文字列を逆順にする
            caption_name = self.caption_names[i][::-1]
            caption_name = caption_name.replace("NNNN", tif_number_str[::-1], 1)
            self.printThread.emit("    [INFO]Modifying animation file name " + str(i + 1) + "/" + str(len(self.caption_names)))

            # 文字列を再度逆順にし元に戻す
            caption_name = caption_name[::-1]
            dist_path = os.path.join(self.light_dirs[i] , "result.mov")
            shutil.move(dist_path,caption_name)

            #remove
            os.remove(self.caption_names[i])
            os.remove(self.light_dirs[i] + '/nocaption.mov')
            self.printThread.emit("    [INFO]Temporary file deleted. " + str(i + 1) + "/" + str(len(self.caption_names)))
            

        for dir_path in self.light_dirs:
            self.printThread.emit("    [INFO]Modifying file name in local folder")
            dist_dir = dir_path.replace("NNNN",tif_number_str)
            shutil.move(dir_path,dist_dir)

        for dir_path in self.light_dirs:
            self.printThread.emit("    [INFO]Modifying Metadata file name. " + str(i + 1) + "/" + str(len(self.caption_names)))
            path = os.path.join(dir_path,"Metadata","*").replace("NNNN",tif_number_str.zfill(4))
            files = glob.glob(path)
            for file in files:
                dist_file = file.replace("NNNN",tif_number_str.zfill(4))
                
                shutil.move(file,dist_file)
                self.printThread.emit("    [INFO]Modifying specimen No. (Metadata) " + str(i + 1) + "/" + str(len(self.caption_names)))
                create_logs.replace_logs(dist_file,tif_number_str.zfill(4))


        path = os.path.join(str(Path(dir_path).parent),"Lab_book","*.xlsx")
        
        files = glob.glob(path)
        
        for file in files:
            self.printThread.emit("    [INFO]Modifying specimen No. (Labbook) ")
            create_logs.replace_logs(file,tif_number_str.zfill(4),False)

        if(self.rb_lto_opt != "No"):
            #directory
            for dir_path in self.light_dirs:
                self.printThread.emit("    [INFO]Modifying file name in local folder")
                dist_dir_before = dir_path.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_sei.text())
                dist_dir_after =dist_dir_before.replace("NNNN",tif_number_str)
                
                shutil.move(dist_dir_before,dist_dir_after)

                if(self.rb_lto_opt == "Both"):
                    self.printThread.emit("    [INFO]Modifying file name in local folder")
                    dist_dir_before = dir_path.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_huku.text())
                    dist_dir_after =dist_dir_before.replace("NNNN",tif_number_str)
                    
                    shutil.move(dist_dir_before,dist_dir_after)
            
            #Animation
            #remove
            i = 0
            for caption_name in self.caption_names:
                #Animation copy
                self.printThread.emit("    [INFO]Copying Animation to LTO (primary) " + str(i + 1) + "/" + str(len(self.caption_names)))
                caption_name = caption_name.replace("NNNN",tif_number_str)
                dist_lto_caption = caption_name.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_sei.text())
                dirname, basename = os.path.split(dist_lto_caption)
                i = i + 1
                try:
                    os.mkdir(dirname)
                    self.printThread.emit('    [INFO]' + dirname + " folder creating")
                except:
                    self.printThread.emit('    [WARNING!]' + dirname + " folder already exists")

                shutil.copyfile(caption_name,dist_lto_caption)
                self.printThread.emit("    [INFO]Animation : OK")

                if(self.rb_lto_opt == "Both"):
                    self.printThread.emit("    [INFO]Copying Animation to LTO (duplicate) " + str(i + 1) + "/" + str(len(self.caption_names)))
                    caption_name = caption_name.replace("NNNN",tif_number_str)
                    dist_lto_caption = caption_name.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_huku.text())
                    dirname, basename = os.path.split(dist_lto_caption)
                    i = i + 1
                    try:
                        os.mkdir(dirname)
                        self.printThread.emit('    [INFO]' + dirname + " folder creating")
                    except:
                        self.printThread.emit('    [WARNING!]' + dirname + " folder already exists")

                    shutil.copyfile(caption_name,dist_lto_caption)
                    self.printThread.emit("    [INFO]Animation : OK")
                

            self.metadata_lto_replace(tif_number_str)
            if(self.rb_lto_opt == "Both"):
                self.metadata_lto_replace(tif_number_str,False)

            self.labbook_lto_replace(tif_number_str)
            if(self.rb_lto_opt == "Both"):
                self.labbook_lto_replace(tif_number_str,False)
            self.printThread.emit("[REPLACE MODE END]")

        self.printThread.emit('------------------------------------------')

    def metadata_lto_replace(self,tif_number_str,sei_flag = True):
        
        #Metadata
        #remove
        i = 0
        for caption_name in self.caption_names:
            
            caption_name = caption_name.replace("NNNN",tif_number_str.zfill(4))
            metadata_path, basename = os.path.split(caption_name)
            metadata_path = os.path.join(Path(metadata_path).parent,"Metadata","*.xlsx").replace("NNNN",tif_number_str.zfill(4))
            files = glob.glob(metadata_path)
            
            for file in files:
                metadata_file_path = file

            if(sei_flag == True):
                self.printThread.emit("    [INFO]Copying Metadata to LTO (primary) " + str(i + 1) + "/" + str(len(self.caption_names)))
                delete_metadata_path =os.path.join(Path(metadata_path).parent,"*.xlsx").replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_sei.text()) 
                dist_lto_metadata = metadata_file_path.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_sei.text())
            else:
                self.printThread.emit("    [INFO]Copying Metadata to LTO (duplicate) " + str(i + 1) + "/" + str(len(self.caption_names)))
                delete_metadata_path =os.path.join(Path(metadata_path).parent,"*.xlsx").replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_huku.text()) 
                dist_lto_metadata = metadata_file_path.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_huku.text())
            
            files = glob.glob(delete_metadata_path)
            
            for file in files:
                os.remove(file)

            shutil.copy(metadata_file_path,dist_lto_metadata)
            i = i + 1

    def labbook_lto_replace(self,tif_number_str,sei_flag = True):
        #Labbook
        #remove
        i = 0
        if(sei_flag == True):
            self.printThread.emit("    [INFO]Copying Labbook to LTO (primary) ")
        else:
            self.printThread.emit("    [INFO]Copying Labbook to LTO (duplicate) ")
        for caption_name in self.caption_names:
            caption_name = caption_name.replace("NNNN",tif_number_str.zfill(4))
            metadata_path, basename = os.path.split(caption_name)
            metadata_path = os.path.join(Path(metadata_path).parent.parent,"Lab_book","*.xlsx")
            local_files = glob.glob(metadata_path)
            for local_file in local_files:
                metadata_file_path = local_file

                if(sei_flag == True):
                    dist_lto_metadata = metadata_file_path.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_sei.text())
                else:
                    dist_lto_metadata = metadata_file_path.replace(str(Path(self.OUTPUT_VOLUME).parent),self.ui.l_output_volume_huku.text())
                lto_files = glob.glob(dist_lto_metadata)
                
                for lto_file in lto_files:
                    os.remove(lto_file)

                shutil.copy(metadata_file_path,dist_lto_metadata)
                i = i + 1

    def end_mode(self):
        self.printThread.emit("[TIF MODE END]")
        self.printThread.emit('------------------------------------------')

        if (self.rb_animation_opt == "Yes (All at once)") or (self.rb_animation_opt == "Yes (Append every)"):
            self.printThread.emit("[ANIMATION MODE START]")
            self.printThread.emit("    [INFO]Creating animation")
            self.chat_message_send("Creating animation")
            for i in range(len(self.caption_names)):
                dirname, basename = os.path.split(self.caption_names[i])
                path1 = Path(dirname)
                ssmtemp = os.path.join(path1.parent,"Images_BA","ssmtemp.txt")
                image_ba_txt_path = os.path.join(path1.parent,"Images_BA","image_ba.txt")

                if(os.path.isfile(ssmtemp)):
                    f = open(ssmtemp,"r")
                    self.printThread.emit("    [INFO]Creating animation with ")
                    for line in f:
                        self.printThread.emit("        " + line)
                    f.close()
                    make_animation_select_folder(self.camera_name,self.pixel_shift,self.frame_change,ssmtemp,self.caption_names[i],image_ba_txt_path)
                    os.remove(ssmtemp)
                    os.remove(image_ba_txt_path)


            self.printThread.emit("[ANIMATION MODE END]")
            self.printThread.emit('------------------------------------------')

    def main_loop(self):
        self.input_volume_extra_counter = 0
        while True:
            self.all_files = []

            for ext in ['arw', 'ARW']:
                paths = os.path.join(self.INPUT_VOLUME, '*.{}'.format(ext))
                self.all_files.extend(glob.glob(paths))

            #全ファイル数が16件未満になったら終了。
            if (self.SAMETIME_MODE == False) and (len(self.all_files) < ARW_COMBINATION_NUMBER):
                if(self.input_volume_extra_counter < self.input_volume_extra_max_num - 1):
                    self.input_volume_extra_counter = self.input_volume_extra_counter + 1
                    self.INPUT_VOLUME = self.input_volumes[self.input_volume_extra_counter].text()

                else:
                    self.printThread.emit("    [INFO]Less than " + str(ARW_COMBINATION_NUMBER) + ' files. TIF MODE finished.')
                    self.chat_message_send("Less than " + str(ARW_COMBINATION_NUMBER) + ' files. Converting finished.')
                    self.printThread.emit('[TIF MODE END]')
                    self.printThread.emit('------------------------------------------')

                    self.end_mode()
                    return 0
                    
            else:
                continue_flag =  self.file_name_ranking()
                if(continue_flag == 0):
                    return 0
                
                ###
                # ターゲットファイルをtmpへ移動
                ###
                if(self.SAMETIME_MODE == True):
                    self.printThread.emit("[TIF MODE START]")
                    
                    light_counter = 0
                    dist_counter = 0
                    combo_number = 1
                    dist_path = os.path.join(self.TMP_VOLUME,"tmp*")
                    tmps = glob.glob(str(dist_path))
                    tmps.sort()

                    while True:

                        arw_base_name = []
                        tif_names = []
                        output_arw_paths = []
                        current_wait_time = 0
                        
                        for j in range(self.size -1):
                            tmp_path = os.path.join(self.TMP_VOLUME , 'tmp' + str(j + 1))
                            for k in range(ARW_COMBINATION_NUMBER):
                                basenum = re.findall('[0-9]+', self.sametime_arw_base_name)[0]
                                arw_base_name.append(self.sametime_arw_base_name)
                                arw_base_name_path =  os.path.join(tmp_path , self.sametime_arw_base_name)
                                
                                path = os.path.join(self.INPUT_VOLUME ,self.sametime_arw_base_name)
                                onece_message = True
                                self.ui.b_stop.setDisabled(False)
                                      
                                while True:
                                    if(self.stop_flag == True):
                                        tmp_counter = 0
                                        for l in range(len(tmps)):
                                            files = glob.glob(os.path.join(tmps[l],"*"),  recursive=True)
                                            
                                            if(len(files)>1):
                                                tmp_counter = tmp_counter + 1

                                        if(tmp_counter == 0):
                                            self.end_mode()
                                            return 0
                                        else:
                                            arw_base_name.pop(-1)
                                            self.last_tif_mode(tif_names,combo_number,light_counter,arw_base_name,dist_counter,tmp_counter,output_arw_paths)
                                            self.end_mode()
                                            return 0    
                                    
                                    is_file = os.path.isfile(path)
                                    print("file check:",path,is_file)
                                    if is_file:
                                        time.sleep(KAKIKOMI_TIME)
                                        self.printThread.emit("     [INFO]ARW " + self.sametime_arw_base_name + " captured")
                                        shutil.move(path,arw_base_name_path)

                                        self.sametime_arw_base_name = self.sametime_arw_base_name.replace(str(int(basenum)),str(int(basenum) + 1))
                                
                                        break
                                    else:

                                        now = datetime.datetime.now() # 現在時刻の取得
                                        t = self.ui.timeEdit.time()
                                        total_second = (t.hour() * 60 * 60 )+ (t.minute() * 60) + t.second()
                                        
                                        end_time = now + datetime.timedelta(seconds=total_second)
                                        today = end_time.strftime('%Y/%m/%d/%H/%M/%S') # 現在時刻を年月曜日で表示

                                        if(onece_message):
                                            self.printThread.emit("     [INFO]Awaiting ARW " + self.sametime_arw_base_name + " capture")
                                            if (self.ui.cb_input_volume_change_time.isChecked()) and (len(self.input_volumes) > 1) and (self.input_volumes[self.input_volume_extra_counter + 1].text() != "not selected"):
                                                
                                                self.printThread.emit("     [INFO]"+self.input_volumes[self.input_volume_extra_counter + 1].text() +"will be referred after "+str(t.hour()) + " h" + str(t.minute()) + " min" )
                                                self.printThread.emit("     [INFO]Estimated time: "+str(today))
                                            onece_message = False
                                        current_wait_time = current_wait_time + 5

                                        if(current_wait_time > total_second) and (self.ui.cb_input_volume_change_time.isChecked()):
                                            current_wait_time = 0
                                            if(self.input_volumes[self.input_volume_extra_counter + 1].text() != "not selected"):
                                                onece_message = True
                                                self.input_volume_extra_counter = self.input_volume_extra_counter + 1
                                                self.INPUT_VOLUME = self.input_volumes[self.input_volume_extra_counter].text()
                                                path = os.path.join(self.INPUT_VOLUME ,self.sametime_arw_base_name)
                                                self.printThread.emit("     [INFO]Scheduled time elapsed")
                                                self.printThread.emit("     [INFO]File PATH switched to " + str(path) + " ")

                                            
                                        time.sleep(5)
                                    
                        if(len(self.light_dirs) == 1):
                            for l in range(self.size -1):
                                for i in range(ARW_COMBINATION_NUMBER):
                                    if(ARW_COMBINATION_NUMBER == 1):
                                        dist_arw_path = os.path.join(self.light_dirs[0] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[0] + '_' + self.positions[0] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')
                                    else:
                                        dist_arw_path = os.path.join(self.light_dirs[0] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[0] + '_' + self.positions[0] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')
                                    dist_tif_path = os.path.join(self.light_dirs[0], 'Images_BA' ,  self.ui.e_digital_specimen_number.text() + "_" + self.light_type_names[0] + "_" + self.positions[0] + "_" + str(combo_number).zfill(4)+".tif")

                                    if(light_counter % ARW_COMBINATION_NUMBER == 0):
                                        tif_names.append(dist_tif_path)
                                    
                                    light_counter = light_counter + 1
                                    output_arw_paths.append(dist_arw_path)
                                if(light_counter % ARW_COMBINATION_NUMBER == 0):
                                        combo_number = combo_number + 1
                        else:
                            
                            for i in range(len(arw_base_name)):
                                if(dist_counter >= ARW_COMBINATION_NUMBER * len(self.light_dirs)):
                                    dist_counter = 0
                                    combo_number = combo_number + 1

                                j = dist_counter // ARW_COMBINATION_NUMBER
                                if(ARW_COMBINATION_NUMBER == 1) :
                                    dist_arw_path = os.path.join(self.light_dirs[j] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[j] + '_' + self.positions[j] + "_" + str(combo_number).zfill(4) + '.ARW')
                                else:
                                    dist_arw_path = os.path.join(self.light_dirs[j] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[j] + '_' + self.positions[j] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')

                                dist_tif_path = os.path.join(self.light_dirs[j], 'Images_BA' ,  self.ui.e_digital_specimen_number.text() + "_" + self.light_type_names[j] + "_" + self.positions[j] + "_" + str(combo_number).zfill(4)+".tif")
                                
                                output_arw_paths.append(dist_arw_path)

                                if(light_counter % ARW_COMBINATION_NUMBER == 0):
                                    tif_names.append(dist_tif_path)
                                
                                light_counter = light_counter + 1
                                dist_counter = dist_counter + 1


                        ui_urls_1 = []
                        ui_urls_2 = []
                        for k in range(len(self.innerWidget1.LneEdts)):
                            ui_urls_1.append(self.innerWidget1.LneEdts[k].text())
                            ui_urls_2.append(self.innerWidget2.LneEdts[k].text())
                        
                        arw_base_name = np.array(arw_base_name).reshape((self.size - 1),ARW_COMBINATION_NUMBER)
                        output_arw_paths = np.array(output_arw_paths).reshape((self.size - 1),ARW_COMBINATION_NUMBER)
                        
                        data = {'path':self.TMP_VOLUME,'tif_names': tif_names,'arw_basenames':output_arw_paths.tolist(),'keysmith_urls_1':ui_urls_1,'keysmith_urls_2':ui_urls_2,"camera_name":self.camera_name,"pixel_shift":self.pixel_shift,"frame_change":self.frame_change,"light_type_num":self.LIGHT_TYPE_NUM,"target_paths":arw_base_name.tolist(),"ACN": ARW_COMBINATION_NUMBER}
                        
                        self.printThread.emit("     [INFO]Manipulating Viewer app")
                        self.tif_counter = self.tif_counter + (self.size - 1)
                        self.tif_mode_wait(data)    
                
                else:
                    for i in range(self.arw_base_name.shape[0]):
                        self.printThread.emit("[TIF MODE START]")
                        for j in range(self.arw_base_name.shape[1]):

                            dist_path_1 = os.path.join(self.TMP_VOLUME , 'tmp' + str(j + 1))

                            for k in range(self.arw_base_name.shape[2]):
                                dist_path_2 =  os.path.join(dist_path_1 , self.arw_base_name[i][j][k])
                                if(self.arw_base_name[i][j][k] != ""):
                                    for l in range(self.input_volume_extra_counter,len(self.input_volumes)):
                                        if(os.path.isfile(os.path.join(self.INPUT_VOLUME ,self.arw_base_name[i][j][k]))):
                                            self.printThread.emit("     [INFO]「"+str(os.path.join(self.INPUT_VOLUME ,self.arw_base_name[i][j][k]))+" detected. Moving to the path")
                                            shutil.move(os.path.join(self.INPUT_VOLUME ,self.arw_base_name[i][j][k]),dist_path_2)
                                            break
                                        else:
                                            self.printThread.emit("     [INFO]「"+str(os.path.join(self.INPUT_VOLUME ,self.arw_base_name[i][j][k]))+" can not be detected")
                                            self.input_volume_extra_counter = self.input_volume_extra_counter + 1
                                            self.INPUT_VOLUME = self.input_volumes[self.input_volume_extra_counter].text()
                                            self.printThread.emit("     [INFO]「"+str(os.path.join(self.INPUT_VOLUME ,self.arw_base_name[i][j][k]))+" searching")
                                            
                        self.printThread.emit("     [INFO]Manipulating Viewer app")
                        self.tif_counter = self.tif_counter + (self.size - 1)
                        tif_names = []
                        for j in range((self.size - 1)):
                            tif_names.append(self.output_tif_paths[i,j,0])
                        
                        ui_urls_1 = []
                        ui_urls_2 = []
                        for k in range(len(self.innerWidget1.LneEdts)):
                            ui_urls_1.append(self.innerWidget1.LneEdts[k].text())
                            ui_urls_2.append(self.innerWidget2.LneEdts[k].text())
                        
                        ###
                        # ここから並列化
                        ###
                        data = {'path':self.TMP_VOLUME,'tif_names': tif_names,'arw_basenames':self.output_arw_paths[i,:,:].tolist(),'keysmith_urls_1':ui_urls_1,'keysmith_urls_2':ui_urls_2,"camera_name":self.camera_name,"pixel_shift":self.pixel_shift,"frame_change":self.frame_change,"light_type_num":self.LIGHT_TYPE_NUM,"target_paths": self.arw_base_name[i,:,:].tolist(),"ACN": ARW_COMBINATION_NUMBER}
                        self.tif_mode_wait(data)                
                
        return 0

    def last_tif_mode(self,tif_names,combo_number,light_counter,arw_base_name,dist_counter,tmp_counter,output_arw_paths):
        
        if(len(self.light_dirs) == 1):
            for l in range(tmp_counter):
                for i in range(ARW_COMBINATION_NUMBER):
                    if(ARW_COMBINATION_NUMBER == 1):
                        dist_arw_path = os.path.join(self.light_dirs[0] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[0] + '_' + self.positions[0] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')
                    else:
                        dist_arw_path = os.path.join(self.light_dirs[0] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[0] + '_' + self.positions[0] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')
                    dist_tif_path = os.path.join(self.light_dirs[0], 'Images_BA' ,  self.ui.e_digital_specimen_number.text() + "_" + self.light_type_names[0] + "_" + self.positions[0] + "_" + str(combo_number).zfill(4)+".tif")

                    if(light_counter % ARW_COMBINATION_NUMBER == 0):
                        tif_names.append(dist_tif_path)
                    
                    light_counter = light_counter + 1
                    output_arw_paths.append(dist_arw_path)
                if(light_counter % ARW_COMBINATION_NUMBER == 0):
                        combo_number = combo_number + 1
        else:
            
            for i in range(tmp_counter * ARW_COMBINATION_NUMBER):
                if(dist_counter >= ARW_COMBINATION_NUMBER * len(self.light_dirs)):
                    dist_counter = 0
                    combo_number = combo_number + 1

                j = dist_counter // ARW_COMBINATION_NUMBER
                if(ARW_COMBINATION_NUMBER == 1) :
                    dist_arw_path = os.path.join(self.light_dirs[j] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[j] + '_' + self.positions[j] + "_" + str(combo_number).zfill(4) + '.ARW')
                else:
                    dist_arw_path = os.path.join(self.light_dirs[j] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[j] + '_' + self.positions[j] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')

                dist_tif_path = os.path.join(self.light_dirs[j], 'Images_BA' ,  self.ui.e_digital_specimen_number.text() + "_" + self.light_type_names[j] + "_" + self.positions[j] + "_" + str(combo_number).zfill(4)+".tif")
                
                output_arw_paths.append(dist_arw_path)

                if(light_counter % ARW_COMBINATION_NUMBER == 0):
                    tif_names.append(dist_tif_path)
                
                light_counter = light_counter + 1
                dist_counter = dist_counter + 1

        ui_urls_1 = []
        ui_urls_2 = []
        for k in range(len(self.innerWidget1.LneEdts)):
            ui_urls_1.append(self.innerWidget1.LneEdts[k].text())
            ui_urls_2.append(self.innerWidget2.LneEdts[k].text())
        
        arw_base_name = np.array(arw_base_name).reshape(tmp_counter,ARW_COMBINATION_NUMBER)
        output_arw_paths = np.array(output_arw_paths).reshape(tmp_counter,ARW_COMBINATION_NUMBER)
        
        data = {'path':self.TMP_VOLUME,'tif_names': tif_names,'arw_basenames':output_arw_paths.tolist(),'keysmith_urls_1':ui_urls_1,'keysmith_urls_2':ui_urls_2,"camera_name":self.camera_name,"pixel_shift":self.pixel_shift,"frame_change":self.frame_change,"light_type_num":self.LIGHT_TYPE_NUM,"target_paths":arw_base_name.tolist(),"ACN": ARW_COMBINATION_NUMBER}
        self.printThread.emit("     [INFO]Manipulating Viewer app")
        self.tif_counter = self.tif_counter + tmp_counter
        self.tif_mode_wait_last(data,tmp_counter)

    def tif_mode_wait(self,data):

        self.ui.b_stop.setDisabled(True)
        tif_names = data["tif_names"]
        #isendでnumpyは送ることができない
        for j in range(1, self.size):
            req = self.comm.isend(data, dest=j, tag=j)
            req.wait()

        #各ランクとTIFとARW処理の足並みを揃えるためのireciv
        #rank1-Nの順で、isendを待っている
        for j in range(self.size - 1):
            if(self.ui.cw_tif.isChecked() == True): 	
                self.chat_message_send("Awaiting rank" + str(j + 1) + " TIF process") 
            
            self.printThread.emit("     [INFO]Awaiting rank" + str(j + 1) + " TIF process")

            req = comm.irecv(source=j + 1, tag= j + 11) 	
            data = req.wait()

            if(self.ui.cw_tif.isChecked() == True) and (data == True): 	
                self.chat_message_send("rank" + str(j + 1) + " TIF process done")
            elif(self.ui.cw_tif.isChecked() == True) and (data == False): 	
                self.chat_message_send("rank" + str(j + 1) + " TIF process was not performed")
        
        for j in range((self.size - 1)):
            dirname, basename = os.path.split(tif_names[j])
            ssmtemp = os.path.join(dirname,"ssmtemp.txt")
            with open(ssmtemp, mode='a', newline='\n') as file:
                file.write("file " + "'" + tif_names[j] + "'\n")
            image_ba_txt_path = os.path.join(dirname,"image_ba.txt")
            
            f_ba = open(image_ba_txt_path,'a')
            f_ba.write(tif_names[j] + '\n')
            f_ba.close()

        self.printThread.emit("[TIF MODE END]")
        self.printThread.emit('------------------------------------------')

        ###TIF化処理終了input上にファイルを残さない場合の削除処理を入れる。
        self.remove_files_from_input(True)

        for j in range(len(self.caption_names)):
            #行数確認
            dirname, basename = os.path.split(self.caption_names[j])
            path1 = Path(dirname)
            ssmtemp = os.path.join(path1.parent,"Images_BA","ssmtemp.txt")
            image_ba_txt_path = os.path.join(path1.parent,"Images_BA","image_ba.txt")

            if(self.rb_animation_opt == "Yes (All at once)"):
                self.printThread.emit("[ANIMATION MODE START]")
                self.printThread.emit("    [INFO]Animation will be generated at once after all data processed")
                self.printThread.emit("[ANIMATION MODE END]")
                self.printThread.emit('------------------------------------------')

            elif(self.rb_animation_opt == "Yes (Append every)" and (sum([1 for _ in open(ssmtemp)]) >= int(self.ui.sp_animation_num.value()))):
                self.printThread.emit("[ANIMATION MODE START]")
                self.printThread.emit("    [INFO]Images reached to scheduled amount. Creating animation." + str(self.ui.sp_animation_num.value()))
                
                f = open(ssmtemp,"r")
                self.printThread.emit("    [INFO]Creating animation with ")
                for line in f:
                    self.printThread.emit("        "+line)
                f.close()

                make_animation_select_folder(self.camera_name,self.pixel_shift,self.frame_change,ssmtemp,self.caption_names[j],image_ba_txt_path)
                os.remove(ssmtemp)
                os.remove(image_ba_txt_path)
                self.printThread.emit("[ANIMATION MODE END]")
                self.printThread.emit('------------------------------------------')

    def tif_mode_wait_last(self,data,tmp_counter):
        self.ui.b_stop.setDisabled(True)
        tif_names = data["tif_names"]
        #isendでnumpyは送ることができない
        for j in range(1, tmp_counter+1):
            req = self.comm.isend(data, dest=j, tag=j)
            req.wait()
        
        #各ランクとTIFとARW処理の足並みを揃えるためのireciv
        #rank1-Nの順で、isendを待っている
        for j in range(tmp_counter):
            if(self.ui.cw_tif.isChecked() == True): 	
                self.chat_message_send("Awaiting rank" + str(j + 1) + " TIF process") 
            
            self.printThread.emit("     [INFO]Awaiting rank" + str(j + 1) + " TIF process")

            req = comm.irecv(source=j + 1, tag= j + 11) 	
            data = req.wait()

            if(self.ui.cw_tif.isChecked() == True) and (data == True): 	
                self.chat_message_send("rank" + str(j + 1) + " TIF process done")
            elif(self.ui.cw_tif.isChecked() == True) and (data == False): 	
                self.chat_message_send("rank" + str(j + 1) + " TIF process not performed")
        
        for j in range(tmp_counter):
            dirname, basename = os.path.split(tif_names[j])
            ssmtemp = os.path.join(dirname,"ssmtemp.txt")
            with open(ssmtemp, mode='a', newline='\n') as file:
                file.write("file " + "'" + tif_names[j] + "'\n")
            image_ba_txt_path = os.path.join(dirname,"image_ba.txt")
            
            f_ba = open(image_ba_txt_path,'a')
            f_ba.write(tif_names[j] + '\n')
            f_ba.close()

        self.printThread.emit("[TIF MODE END]")
        self.printThread.emit('------------------------------------------')

        ###TIF化処理終了input上にファイルを残さない場合の削除処理を入れる。
        self.remove_files_from_input(True)

        for j in range(len(self.caption_names)):
            #行数確認
            dirname, basename = os.path.split(self.caption_names[j])
            path1 = Path(dirname)
            ssmtemp = os.path.join(path1.parent,"Images_BA","ssmtemp.txt")
            image_ba_txt_path = os.path.join(path1.parent,"Images_BA","image_ba.txt")

            if(self.rb_animation_opt == "Yes (All at once)"):
                self.printThread.emit("[ANIMATION MODE START]")
                self.printThread.emit("    [INFO]Animation will be generated all at once after all images processed.")
                self.printThread.emit("[ANIMATION MODE END]")
                self.printThread.emit('------------------------------------------')

            elif(self.rb_animation_opt == "Yes (Append every)" and (sum([1 for _ in open(ssmtemp)]) >= int(self.ui.sp_animation_num.value()))):
                self.printThread.emit("[ANIMATION MODE START]")
                self.printThread.emit("    [INFO]No. of images reached to given amount. Generating animation." + str(self.ui.sp_animation_num.value()))
                
                f = open(ssmtemp,"r")
                self.printThread.emit("    [INFO]Generation animation below.")
                for line in f:
                    self.printThread.emit("        "+line)
                f.close()

                make_animation_select_folder(self.camera_name,self.pixel_shift,self.frame_change,ssmtemp,self.caption_names[j],image_ba_txt_path)
                os.remove(ssmtemp)
                os.remove(image_ba_txt_path)
                self.printThread.emit("[ANIMATION MODE END]")
                self.printThread.emit('------------------------------------------')

    def remove_files_from_input(self,first_flag = False):
        time.sleep(3)
        for i in range(len(self.caption_names)):
            dirname, basename = os.path.split(self.caption_names[i])
            path1 = Path(dirname)

            if(self.ui.cb_write_arw_2.isChecked() == False):
                self.printThread.emit("[REMOVE MODE(ARW) START]")
                if(first_flag == False):
                    if(ARW_COMBINATION_NUMBER == 1):
                        self.printThread.emit("    [INFO]Removing Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) + ' ')
                        dist_path = os.path.join(path1.parent,"Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1))
                    else:
                        self.printThread.emit("    [INFO]Removing Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) + ' ')
                        dist_path = os.path.join(path1.parent,"Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER))
                    shutil.rmtree(dist_path)
                else:
                    if(ARW_COMBINATION_NUMBER == 1):
                        self.printThread.emit("    [INFO]Removing Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) + ' ')
                        files = glob.glob(os.path.join(path1.parent,"Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1),'*.ARW'))
                    else:
                        self.printThread.emit("    [INFO]Removing Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) + ' ')
                        files = glob.glob(os.path.join(path1.parent,"Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER),'*.ARW'))
                    for file in files:
                        try:
                            os.remove(file)
                        except OSError as e:
                            pass
                
                self.printThread.emit("[REMOVE MODE(ARW) END]")

            if(self.ui.cb_write_tif_2.isChecked() == False):
                self.printThread.emit("[REMOVE MODE(TIF) START]")
                if(first_flag == False):
                    self.printThread.emit("    [INFO]Removing Images")
                    dist_path = os.path.join(path1.parent,"Images_BA")
                    shutil.rmtree(dist_path)
                
                else:
                    self.printThread.emit("    [INFO]Removing Images")
                    files = glob.glob(os.path.join(path1.parent,"Images_BA",'*.tif'))
                    for file in files:
                        try:
                            os.remove(file)
                        except OSError as e:
                            pass
                
                self.printThread.emit("[REMOVE(TIF) MODE END]")
                

            #初回以外での削除動作
            if(first_flag == False):
                if(self.ui.cb_write_animation_2.isChecked() == False):

                    self.printThread.emit("[REMOVE MODE(Animation) START]")
                    self.printThread.emit("    [INFO]Removing Animation")
                    dist_path = os.path.join(path1.parent,"Animation")
                    shutil.rmtree(dist_path)           
                    self.printThread.emit("[REMOVE(Animation) MODE END]")

                if(self.ui.cb_write_meta_2.isChecked() == False):
                    self.printThread.emit("[REMOVE MODE(Metadata) START]")
                    self.printThread.emit("    [INFO]Removing Metadata")
                    dist_path = os.path.join(path1.parent,"Metadata")
                    shutil.rmtree(dist_path) 

                    self.printThread.emit("[REMOVE(Metadata) MODE END]")

                #if parent dir is empty
                try:
                    os.rmdir(path1.parent)
                except OSError as e:
                    pass

                if(self.ui.cb_write_lab_2.isChecked() == False):
                    self.printThread.emit("[REMOVE MODE(Lab Book) START]")
                    self.printThread.emit("    [INFO]Removing Lab Book")
                    dist_path = os.path.join(path1.parent.parent,"Lab_book")
                    shutil.rmtree(dist_path)

                    self.printThread.emit("[REMOVE(Lab Book) MODE END]")

                try:
                    os.remove(os.path.join(path1.parent.parent,"exclude_files_sei.txt")) 
                except:
                    pass
                
                try:
                    os.remove(os.path.join(path1.parent.parent,"exclude_files_huku.txt")) 
                except:
                    pass

                self.printThread.emit("[REMOVE MODE START]")
                self.printThread.emit("    [INFO]Removing tmp*")

                dist_path = os.path.join(self.TMP_VOLUME,"tmp*")
                
                tmps = glob.glob(str(dist_path))
                try:
                    for k in range(0,len(tmps)):
                        self.printThread.emit("     [INFO]Removing " + tmps[k] + " ")
                        shutil.rmtree(tmps[k])
                    
                except:
                    self.printThread.emit("     [INFO]An error ocurred during removing")

                tif_number_str = str(int(self.tif_counter/self.LIGHT_TYPE_NUM)).zfill(4)
                self.printThread.emit("    [INFO]Removing Images_BA")
                try:
                    dist_dir = str(path1.parent).replace("NNNN",tif_number_str)
                    shutil.rmtree(os.path.join(dist_dir,"Images_BA"))
                
                except:
                    self.printThread.emit("     [INFO]An error occurred during removing")

                self.printThread.emit("[REMOVE MODE END]")

            
                self.printThread.emit('------------------------------------------')

    def create_dir_log(self,light_dir,metadata_path,light_mode,temperature,voxel,meta_name,grinding_tools):
        self.printThread.emit("[DIRECTORY MODE START]")
        if(ARW_COMBINATION_NUMBER == 1):
            dir_list = ["Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1),'Images_BA','Images','Animation','Metadata']
        else:
            dir_list = ["Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER),'Images_BA','Images','Animation','Metadata']

        try:
            os.mkdir(light_dir)
            self.printThread.emit('    [INFO]Creating ' + light_dir + " ")
        except:
            self.printThread.emit('    [WARNING!]Created: ' + light_dir + " ")
        
        #内部フォルダ作成
        for dir in dir_list:
            try:
                os.mkdir(light_dir + '/' + dir)
                self.printThread.emit('    [INFO]Creating ' + light_dir + '/' + dir + " ")
            except:
                self.printThread.emit('    [WARNING!]Created ' + light_dir + '/' + dir + " ")
            
        time.sleep(3)   #Error Prevention
        self.printThread.emit("[DIRECTORY MODE END]")
        self.printThread.emit('------------------------------------------')
        self.printThread.emit("[CREATE LOG MODE START]")
        CreateLog.metadata(self,self.selected_mode,metadata_path,light_mode,temperature,voxel,meta_name,grinding_tools)
        self.printThread.emit("     [INFO]Log creted")
        self.printThread.emit("[CREATE LOG MODE END]")
        self.printThread.emit('------------------------------------------')
        

    def chat_message_send(self,message):
        URL = 'https://api.chatwork.com/v2'
        url = URL + '/rooms/' + self.ui.e_chatwork_room_id.text() + '/messages'
        headers = { 'X-ChatWorkToken': self.ui.e_chatwork_api_key.text() }
        params = { 'body': message }
        try:
            resp = requests.post(url,headers=headers,params=params)
        except:  
           self.printThread.emit("[ERROR!]An error occurred during chatwork communication")

    #各ランクごとのファイル名を設定
    def file_name_ranking(self):
        self.sametime_arw_base_name = ""
        arw_base_name = []
        dir_paths = [self.INPUT_VOLUME]
        dir_list = []
        for i in range(len(self.cb_ins)):
            if((self.cb_ins[i].checkState() != 0) and (self.l_input_volumes[i].text() != "not selected")):
                dir_paths.append(self.l_input_volumes[i].text())

        for dir_path in dir_paths:
            files = os.listdir(dir_path)
            for file in files:
                dir_list.append(file)
        output_arw_paths_l = []
        output_tif_paths_l = []

        if(self.SAMETIME_MODE == True):
            arw_names = glob.glob(os.path.join(self.INPUT_VOLUME,'*.ARW'))
            arw_names.sort()
            if(len(arw_names) == 0):               
                self.printThread.emit("[MESSAGE]Awaiting 1st ARW capture")     
                while True:
                    time.sleep(KAKIKOMI_TIME)
                    arw_names = glob.glob(os.path.join(self.INPUT_VOLUME,'*.ARW'))
                    if(len(arw_names) != 0):
                        arw_names.sort()
                        self.printThread.emit("[MESSAGE]1st ARW captured.")
                        self.sametime_arw_base_name = os.path.basename(arw_names[0])
                        break
            else:
                self.printThread.emit("[MESSAGE]1st ARW captured.")
                self.sametime_arw_base_name = os.path.basename(arw_names[0])
            
        else:
            for i in range(len(dir_list)):
                if (".ARW" == os.path.splitext(dir_list[i])[1]) or (".arw" == os.path.splitext(dir_list[i])[1]): ## os.path.splitext()[1]で拡張子を取得
                    arw_base_name.append(dir_list[i])

            arw_base_name.sort()
            
            light_counter = 0
            dist_counter = 0

            if(len(self.light_dirs) == 1):
                combo_number = 0
                for i in range(len(arw_base_name)):
                    if(light_counter % ARW_COMBINATION_NUMBER == 0):
                        combo_number = combo_number + 1
                    if(ARW_COMBINATION_NUMBER == 1):
                        dist_arw_path = os.path.join(self.light_dirs[0] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[0] + '_' + self.positions[0] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')
                    else:
                        dist_arw_path = os.path.join(self.light_dirs[0] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[0] + '_' + self.positions[0] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')
                    dist_tif_path = os.path.join(self.light_dirs[0], 'Images_BA' ,  self.ui.e_digital_specimen_number.text() + "_" + self.light_type_names[0] + "_" + self.positions[0] + "_" + str(combo_number).zfill(4)+".tif")

                    output_arw_paths_l.append(dist_arw_path)

                    if(light_counter % ARW_COMBINATION_NUMBER == 0):
                        output_tif_paths_l.append(dist_tif_path)

                    light_counter = light_counter + 1

            else:
                combo_number = 1
                for i in range(len(arw_base_name)):
                    if(dist_counter >= ARW_COMBINATION_NUMBER * len(self.light_dirs)):
                        dist_counter = 0
                        combo_number = combo_number + 1

                    j = dist_counter // ARW_COMBINATION_NUMBER

                    if(ARW_COMBINATION_NUMBER == 1) :
                        dist_arw_path = os.path.join(self.light_dirs[j] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER-1) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[j] + '_' + self.positions[j] + "_" + str(combo_number).zfill(4) + '.ARW')
                    else:
                        dist_arw_path = os.path.join(self.light_dirs[j] , "Rawdata_PSMS_" + str(ARW_COMBINATION_NUMBER) , self.ui.e_digital_specimen_number.text() + '_' + self.light_type_names[j] + '_' + self.positions[j] + "_" + str(combo_number).zfill(4) + '_' + str(light_counter % ARW_COMBINATION_NUMBER + 1).zfill(2) + '.ARW')

                    dist_tif_path = os.path.join(self.light_dirs[j], 'Images_BA' ,  self.ui.e_digital_specimen_number.text() + "_" + self.light_type_names[j] + "_" + self.positions[j] + "_" + str(combo_number).zfill(4)+".tif")
                    
                    output_arw_paths_l.append(dist_arw_path)

                    if(light_counter % ARW_COMBINATION_NUMBER == 0):
                        output_tif_paths_l.append(dist_tif_path)
                    
                    light_counter = light_counter + 1
                    dist_counter = dist_counter + 1

            #reshapeする際にエラーが出ないように空欄があれば穴埋めする
            if(len(arw_base_name) % ((self.size - 1) * ARW_COMBINATION_NUMBER) != 0):
                for i in range(((self.size - 1) * ARW_COMBINATION_NUMBER) - (len(arw_base_name) % ((self.size - 1) * ARW_COMBINATION_NUMBER))):
                    arw_base_name.append("")

            if(len(output_arw_paths_l) % ((self.size - 1) * ARW_COMBINATION_NUMBER) != 0):
                for i in range(((self.size - 1) * ARW_COMBINATION_NUMBER) - (len(output_arw_paths_l) % ((self.size - 1) * ARW_COMBINATION_NUMBER))):
                    output_arw_paths_l.append("")

            if(len(output_tif_paths_l) % ((self.size - 1)) != 0):
                for i in range(((self.size - 1)) - (len(output_tif_paths_l) % (self.size - 1))):
                    output_tif_paths_l.append("")

            self.arw_base_name = np.array(arw_base_name)
            self.output_arw_paths = np.array(output_arw_paths_l)
            self.output_tif_paths = np.array(output_tif_paths_l)
            
            self.arw_base_name = self.arw_base_name.reshape(int(len(arw_base_name)/((self.size - 1) * ARW_COMBINATION_NUMBER)),(self.size - 1),ARW_COMBINATION_NUMBER)
            self.output_arw_paths = self.output_arw_paths.reshape(int(len(output_arw_paths_l)/((self.size - 1) * ARW_COMBINATION_NUMBER)),(self.size - 1),ARW_COMBINATION_NUMBER)
            self.output_tif_paths = self.output_tif_paths.reshape(int(len(output_tif_paths_l)/(self.size - 1)),(self.size - 1),1)





def make_animation_select_folder(camera_name,pixel_shift,frame_change,ssmtemp,caption_name,image_ba_txt_path):
    dirname, basename = os.path.split(caption_name)
    output_row_path = os.path.join(dirname,"row.mov")
    sep = '_'
    t = basename.split(sep)  # 半角空白文字で文字列を分割
    numberingcaption = t[0] + "_" + t[1] + "_" + t[2] + "_" 

    # ①I32で選択した機種が5Dsか5DsRの場合：NMB_XPOS=50, NMB_YPOS=5642, NMB_SIZE=100, PHOTOSIZE=8K
    # ②I32で選択した機種がa7RIV，I38の値がnotかPSMS4の場合：NMB_XPOS=55, NMB_YPOS=6171, NMB_SIZE=110, PHOTOSIZE=9K
    # ③I32で選択した機種がa7RIV，I38の値がPSMS16の場合： NMB_XPOS=119, NMB_YPOS=12342, NMB_SIZE=220, PHOTOSIZE=19K
    # ④GFXかつI38がnotの場合 NMB_XPOS=67, NMB_YPOS=4283, NMB_SIZE=135
    # ⑤GFXかつI38がPSMS16の場合 NMB_XPOS=135, NMB_YPOS=8566, NMB_SIZE=270

    if("α7R IV" in camera_name):
        if(pixel_shift == "not") or (pixel_shift == "PSMS4"):
            NMB_XPOS=55
            NMB_YPOS=6171
            NMB_SIZE=110
        else:
            NMB_XPOS=119
            NMB_YPOS=12342
            NMB_SIZE=220

    elif("GFX" in camera_name):
        if(pixel_shift == "not"):
            NMB_XPOS=67
            NMB_YPOS=4283
            NMB_SIZE=135
        else:
            NMB_XPOS=135
            NMB_YPOS=8566
            NMB_SIZE=270
    else:
        NMB_XPOS=50
        NMB_YPOS=5642
        NMB_SIZE=100

    if(frame_change == True):
        width = 4344
        height = 3258

    else:
        width = 4344
        height = 2896

    font = os.path.join(os.getcwd() , 'template','fonts','PT_Serif','PTSerif-Regular.ttf')
    numberingcaption = " -vf \"drawtext=fontfile=" + str(font) + ": text=\'" + str(numberingcaption) + "%{eif\:n+1\:d\:4}\': r=25: x=" + str(NMB_XPOS) + ": y=" + str(NMB_YPOS) + ": fontsize=" + str(NMB_SIZE) + ": fontcolor=white: box=1: boxcolor=0x00000099\""
    fps = 15
    ssmsize = str(width) + "x" + str(height)

    command = 'ffmpeg -y -loglevel quiet -f concat -r 15 -safe 0'\
    + ' -i ' + str(ssmtemp) + ' -r ' + str(fps)\
    + ' -s ' + str(ssmsize) \
    + '  -pix_fmt yuv420p -vcodec mjpeg -b:v 600000000000000'\
    + str(numberingcaption)\
    + ' "' + output_row_path + '"'

    subprocess.call(command, shell=True)

    subprocess.call('ffmpeg -loglevel quiet -i ' + caption_name + ' -i ' + output_row_path + ' -vcodec mjpeg -pix_fmt yuv420p -b:v 600000000000000 -r 15 -filter_complex concat ' + "result.mov" ,shell=True)   
    shutil.move("result.mov",caption_name)

    os.remove(output_row_path)

    with open(image_ba_txt_path) as f:
        for ba_path in f:
            path_re =ba_path.replace("\n","")
            shutil.move(Path(path_re),os.path.join(Path(path_re).parent.parent,"Images",os.path.basename(path_re)))
    
    

    time.sleep(3)
