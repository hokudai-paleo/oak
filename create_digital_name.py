from PyQt5.QtCore import pyqtSignal
import os

import ui

ARW_COMBINATION_NUMBER = 16

class CreateDN():
    
    textBrowser = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(CreateDN, self).__init__(parent)
        self.ui = ui.Ui_Form()
        self.ui.setupUi(self)

    #照明番号を取得する
    def search_light(self,target_light_num,target_position_num):
        if (target_light_num == ""):#未入力
            return "None"
        elif(self.ui.cb_same_time_mode.isChecked()):
            try:
                return self.ui.e_digital_specimen_number.text() + "_" + self.light_pares[int(target_light_num)-1] + "_" + str(target_position_num).zfill(2) + "_" + "0001-NNNN"
            except:
                return "error"
        else:
            try:
                return self.ui.e_digital_specimen_number.text() + "_" + self.light_pares[int(target_light_num)-1] + "_" + str(target_position_num).zfill(2) + "_" + "0001-" + str(self.picture_nums).zfill(4)
            except:
                return "error"

    def display_name(self):

        self.picture_nums = 0

        global ARW_COMBINATION_NUMBER

        if(self.ui.comb_pixel_shift_nulti_shooting.currentText() == "PSMS16"):
            ARW_COMBINATION_NUMBER = 16
        elif(self.ui.comb_pixel_shift_nulti_shooting.currentText() == "PSMS4"):
            ARW_COMBINATION_NUMBER = 4
        else: #self.ui.comb_pixel_shift_nulti_shooting.currentText() == "not"
            ARW_COMBINATION_NUMBER = 1

        try:
            initial_count = 0
            dir = self.ui.l_input_volume.text()
            dirs = []

            for path in os.listdir(dir):
                if os.path.isfile(os.path.join(dir, path))  and (".ARW" in path):
                    initial_count += 1

            for i in range(len(self.cb_ins)):
                if((self.cb_ins[i].checkState() != 0) and (self.l_input_volumes[i].text() != "not selected")):
                    dirs.append(self.l_input_volumes[i].text())
        
            for d in dirs:
                for path in os.listdir(d):
                    
                    if os.path.isfile(os.path.join(d, path)) and (".ARW" in path):
                        initial_count += 1
            
            self.picture_nums = initial_count // (ARW_COMBINATION_NUMBER * self.active_lane_numbers)

        except:
            pass

        #波長および撮影位置を取得
        self.ui.l_d_n_1.setText(CreateDN.search_light(self,self.ui.e_light_1.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_2.setText(CreateDN.search_light(self,self.ui.e_light_2.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_3.setText(CreateDN.search_light(self,self.ui.e_light_3.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_4.setText(CreateDN.search_light(self,self.ui.e_light_4.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_5.setText(CreateDN.search_light(self,self.ui.e_light_5.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_6.setText(CreateDN.search_light(self,self.ui.e_light_6.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_7.setText(CreateDN.search_light(self,self.ui.e_light_7.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_8.setText(CreateDN.search_light(self,self.ui.e_light_8.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_9.setText(CreateDN.search_light(self,self.ui.e_light_9.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_10.setText(CreateDN.search_light(self,self.ui.e_light_10.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_11.setText(CreateDN.search_light(self,self.ui.e_light_11.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_12.setText(CreateDN.search_light(self,self.ui.e_light_12.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_13.setText(CreateDN.search_light(self,self.ui.e_light_13.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_14.setText(CreateDN.search_light(self,self.ui.e_light_14.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_15.setText(CreateDN.search_light(self,self.ui.e_light_15.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_16.setText(CreateDN.search_light(self,self.ui.e_light_16.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_17.setText(CreateDN.search_light(self,self.ui.e_light_17.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_18.setText(CreateDN.search_light(self,self.ui.e_light_18.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_19.setText(CreateDN.search_light(self,self.ui.e_light_19.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_20.setText(CreateDN.search_light(self,self.ui.e_light_20.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_21.setText(CreateDN.search_light(self,self.ui.e_light_21.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_22.setText(CreateDN.search_light(self,self.ui.e_light_22.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_23.setText(CreateDN.search_light(self,self.ui.e_light_23.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_24.setText(CreateDN.search_light(self,self.ui.e_light_24.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_25.setText(CreateDN.search_light(self,self.ui.e_light_25.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_26.setText(CreateDN.search_light(self,self.ui.e_light_26.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_27.setText(CreateDN.search_light(self,self.ui.e_light_27.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_28.setText(CreateDN.search_light(self,self.ui.e_light_28.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_29.setText(CreateDN.search_light(self,self.ui.e_light_29.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_30.setText(CreateDN.search_light(self,self.ui.e_light_30.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_31.setText(CreateDN.search_light(self,self.ui.e_light_31.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_32.setText(CreateDN.search_light(self,self.ui.e_light_32.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_33.setText(CreateDN.search_light(self,self.ui.e_light_33.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_34.setText(CreateDN.search_light(self,self.ui.e_light_34.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_35.setText(CreateDN.search_light(self,self.ui.e_light_35.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_36.setText(CreateDN.search_light(self,self.ui.e_light_36.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_37.setText(CreateDN.search_light(self,self.ui.e_light_37.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_38.setText(CreateDN.search_light(self,self.ui.e_light_38.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_39.setText(CreateDN.search_light(self,self.ui.e_light_39.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_40.setText(CreateDN.search_light(self,self.ui.e_light_40.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_41.setText(CreateDN.search_light(self,self.ui.e_light_41.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_42.setText(CreateDN.search_light(self,self.ui.e_light_42.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_43.setText(CreateDN.search_light(self,self.ui.e_light_43.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_44.setText(CreateDN.search_light(self,self.ui.e_light_44.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_45.setText(CreateDN.search_light(self,self.ui.e_light_45.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_46.setText(CreateDN.search_light(self,self.ui.e_light_46.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_47.setText(CreateDN.search_light(self,self.ui.e_light_47.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_48.setText(CreateDN.search_light(self,self.ui.e_light_48.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_49.setText(CreateDN.search_light(self,self.ui.e_light_49.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_50.setText(CreateDN.search_light(self,self.ui.e_light_50.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_51.setText(CreateDN.search_light(self,self.ui.e_light_51.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_52.setText(CreateDN.search_light(self,self.ui.e_light_52.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_53.setText(CreateDN.search_light(self,self.ui.e_light_53.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_54.setText(CreateDN.search_light(self,self.ui.e_light_54.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_55.setText(CreateDN.search_light(self,self.ui.e_light_55.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_56.setText(CreateDN.search_light(self,self.ui.e_light_56.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_57.setText(CreateDN.search_light(self,self.ui.e_light_57.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_58.setText(CreateDN.search_light(self,self.ui.e_light_58.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_59.setText(CreateDN.search_light(self,self.ui.e_light_59.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_60.setText(CreateDN.search_light(self,self.ui.e_light_60.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_61.setText(CreateDN.search_light(self,self.ui.e_light_61.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_62.setText(CreateDN.search_light(self,self.ui.e_light_62.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_63.setText(CreateDN.search_light(self,self.ui.e_light_63.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_64.setText(CreateDN.search_light(self,self.ui.e_light_64.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_65.setText(CreateDN.search_light(self,self.ui.e_light_65.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_66.setText(CreateDN.search_light(self,self.ui.e_light_66.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_67.setText(CreateDN.search_light(self,self.ui.e_light_67.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_68.setText(CreateDN.search_light(self,self.ui.e_light_68.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_69.setText(CreateDN.search_light(self,self.ui.e_light_69.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_70.setText(CreateDN.search_light(self,self.ui.e_light_70.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_71.setText(CreateDN.search_light(self,self.ui.e_light_71.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_72.setText(CreateDN.search_light(self,self.ui.e_light_72.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_73.setText(CreateDN.search_light(self,self.ui.e_light_73.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_74.setText(CreateDN.search_light(self,self.ui.e_light_74.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_75.setText(CreateDN.search_light(self,self.ui.e_light_75.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_76.setText(CreateDN.search_light(self,self.ui.e_light_76.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_77.setText(CreateDN.search_light(self,self.ui.e_light_77.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_78.setText(CreateDN.search_light(self,self.ui.e_light_78.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_79.setText(CreateDN.search_light(self,self.ui.e_light_79.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_80.setText(CreateDN.search_light(self,self.ui.e_light_80.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_81.setText(CreateDN.search_light(self,self.ui.e_light_81.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_82.setText(CreateDN.search_light(self,self.ui.e_light_82.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_83.setText(CreateDN.search_light(self,self.ui.e_light_83.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_84.setText(CreateDN.search_light(self,self.ui.e_light_84.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_85.setText(CreateDN.search_light(self,self.ui.e_light_85.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_86.setText(CreateDN.search_light(self,self.ui.e_light_86.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_87.setText(CreateDN.search_light(self,self.ui.e_light_87.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_88.setText(CreateDN.search_light(self,self.ui.e_light_88.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_89.setText(CreateDN.search_light(self,self.ui.e_light_89.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_90.setText(CreateDN.search_light(self,self.ui.e_light_90.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_91.setText(CreateDN.search_light(self,self.ui.e_light_91.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_92.setText(CreateDN.search_light(self,self.ui.e_light_92.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_93.setText(CreateDN.search_light(self,self.ui.e_light_93.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_94.setText(CreateDN.search_light(self,self.ui.e_light_94.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_95.setText(CreateDN.search_light(self,self.ui.e_light_95.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_96.setText(CreateDN.search_light(self,self.ui.e_light_96.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_97.setText(CreateDN.search_light(self,self.ui.e_light_97.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_98.setText(CreateDN.search_light(self,self.ui.e_light_98.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_99.setText(CreateDN.search_light(self,self.ui.e_light_99.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_100.setText(CreateDN.search_light(self,self.ui.e_light_100.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_101.setText(CreateDN.search_light(self,self.ui.e_light_101.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_102.setText(CreateDN.search_light(self,self.ui.e_light_102.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_103.setText(CreateDN.search_light(self,self.ui.e_light_103.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_104.setText(CreateDN.search_light(self,self.ui.e_light_104.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_105.setText(CreateDN.search_light(self,self.ui.e_light_105.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_106.setText(CreateDN.search_light(self,self.ui.e_light_106.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_107.setText(CreateDN.search_light(self,self.ui.e_light_107.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_108.setText(CreateDN.search_light(self,self.ui.e_light_108.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_109.setText(CreateDN.search_light(self,self.ui.e_light_109.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_110.setText(CreateDN.search_light(self,self.ui.e_light_110.text(),self.ui.e_position_no_10.text()))

        self.ui.l_d_n_111.setText(CreateDN.search_light(self,self.ui.e_light_111.text(),self.ui.e_position_no_1.text()))
        self.ui.l_d_n_112.setText(CreateDN.search_light(self,self.ui.e_light_112.text(),self.ui.e_position_no_2.text()))
        self.ui.l_d_n_113.setText(CreateDN.search_light(self,self.ui.e_light_113.text(),self.ui.e_position_no_3.text()))
        self.ui.l_d_n_114.setText(CreateDN.search_light(self,self.ui.e_light_114.text(),self.ui.e_position_no_4.text()))
        self.ui.l_d_n_115.setText(CreateDN.search_light(self,self.ui.e_light_115.text(),self.ui.e_position_no_5.text()))
        self.ui.l_d_n_116.setText(CreateDN.search_light(self,self.ui.e_light_116.text(),self.ui.e_position_no_6.text()))
        self.ui.l_d_n_117.setText(CreateDN.search_light(self,self.ui.e_light_117.text(),self.ui.e_position_no_7.text()))
        self.ui.l_d_n_118.setText(CreateDN.search_light(self,self.ui.e_light_118.text(),self.ui.e_position_no_8.text()))
        self.ui.l_d_n_119.setText(CreateDN.search_light(self,self.ui.e_light_119.text(),self.ui.e_position_no_9.text()))
        self.ui.l_d_n_120.setText(CreateDN.search_light(self,self.ui.e_light_120.text(),self.ui.e_position_no_10.text()))


def light_changer(target_text):
    if(target_text == "PA") or (target_text == "PB") or (target_text == "GN6000") or (target_text == "GN9000")  or (target_text == "RL6000") or (target_text == "RL9000") or (target_text == "RLS") or (target_text == "RLL"):

        result = "wl"
    elif(target_text == "HP-365") or (target_text == "SP365"):

        result = "uv365nm"

    elif(target_text == "SP530"):
        result = "uv530nm"

    elif(target_text == "SP590"):
        result = "uv590nm"

    else:
        result = ""

    return result