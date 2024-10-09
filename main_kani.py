#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import configparser
import requests
import glob
import itertools
import shutil
import time
from PyQt5.QtWidgets import QDialog, QApplication,QFileDialog,QMessageBox,QLineEdit,QWidget,QSpacerItem,QSizePolicy,QGridLayout,QLabel
from PyQt5.QtCore import QDate
from decimal import Decimal, ROUND_HALF_UP

import subprocess

import webbrowser

import check_input
import create_digital_name
import show_table
from start_pushed import ActionThread
from sync_thread import SyncThread
from create_logs import CreateLog
import ui

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
name = MPI.Get_processor_name()

ARW_COMBINATION_NUMBER = 16 


class Keysmith1Widget(QWidget):
    def __init__(self, *args, **kwargs):
        super(Keysmith1Widget, self).__init__(*args, **kwargs)    
        
        self.LneEdts = {}
        self.LneEdts[0] = QLineEdit()
        self.indx = 0
        self.mainLayout = QGridLayout(self)
        self.verticalSpacer = None

    def SetImage(self):
        if(size > self.indx):
            if self.verticalSpacer != None:
                self.mainLayout.removeItem(self.verticalSpacer)

            self.LneEdts[self.indx] = QLineEdit()
            label = QLabel()
            label.setText("URL" + str(self.indx + 1))

            self.mainLayout.addWidget(label,self.indx,0)
            self.mainLayout.addWidget(self.LneEdts[self.indx],self.indx,1)
            
            self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum,QSizePolicy.Expanding)
            self.mainLayout.addItem(self.verticalSpacer)

            self.indx = self.indx + 1
        
        else:
            if self.verticalSpacer != None:
                self.mainLayout.removeItem(self.verticalSpacer)
            label = QLabel()
            label.setText("入力欄がsize数の上限に達しています。")
            self.mainLayout.addWidget(label,self.indx,1)
            self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum,QSizePolicy.Expanding)
            self.mainLayout.addItem(self.verticalSpacer)

class MyForm(QDialog):
    def __init__(self, parent=None):
        super(MyForm, self).__init__(parent)
        self.ui = ui.Ui_e_notes_2()
        self.ui.setupUi(self)

        #メインボタンのクリック動作
        self.ui.b_start.clicked.connect(self.ui.b_start.toggle)
        self.ui.b_start.clicked.connect(self.exec_button)
        self.ui.b_stop.clicked.connect(self.stop_button)
        self.ui.b_export.clicked.connect(self.setting_output)
        self.ui.b_import.clicked.connect(self.setting_input)
        self.ui.b_log_output.clicked.connect(self.log_re_output)

        self.ui.b_pause.clicked.connect(self.stop_loop)

        #入出力設定用ボタン
        self.ui.b_output_volume_sei.clicked.connect(self.output_volume_setting_sei)
        self.ui.b_output_volume_huku.clicked.connect(self.output_volume_setting_huku)
        self.ui.b_input_volume.clicked.connect(self.input_volume_setting)
        self.ui.b_output_volume.clicked.connect(self.output_volume_setting)
        self.ui.b_output_volume_reset.clicked.connect(self.output_volume_setting_reset)
        #1
        self.ui.b_tmp_volume.clicked.connect(self.tmp_volume_setting)
        self.ui.b_tmp_volume_reset.clicked.connect(self.tmp_volume_setting_reset)

        #ラジオボタンによる動作
        self.ui.rb_bioligical_sample.toggled.connect(self.rb_clicked)
        self.ui.rb_rock_sample.toggled.connect(self.rb_clicked)
        self.ui.rb_other_sample.toggled.connect(self.rb_clicked)
        
        self.ui.rb_animation_no.toggled.connect(self.rb_animation)
        self.ui.rb_animation_num.toggled.connect(self.rb_animation)
        self.ui.rb_animation_all.toggled.connect(self.rb_animation)
        
        self.ui.rb_sei.toggled.connect(self.rb_lto)
        self.ui.rb_seifuku.toggled.connect(self.rb_lto)
        self.ui.rb_seifuku_nashi.toggled.connect(self.rb_lto)

        self.ui.rb_nokosu.toggled.connect(self.rb_input)
        self.ui.rb_nokosanai.toggled.connect(self.rb_input)
        
        self.ui.rb_full.toggled.connect(self.rb_full_select)
        self.ui.rb_nofull.toggled.connect(self.rb_full_select)

        self.ui.rb_lto_dev_num_sei_0.toggled.connect(self.rb_lto_number)
        self.ui.rb_lto_dev_num_sei_1.toggled.connect(self.rb_lto_number)
        self.ui.rb_lto_dev_num_huku_0.toggled.connect(self.rb_lto_number)
        self.ui.rb_lto_dev_num_huku_1.toggled.connect(self.rb_lto_number)


        #テキストエディタの有効/無効設定
        self.ui.rb_dataset_active.toggled.connect(self.rb_dataset_active_clicked)
        self.ui.rb_dataset_disactive.toggled.connect(self.rb_dataset_active_clicked)
        self.ui.rb_voxel_active.toggled.connect(self.rb_voxel_active_clicked)
        self.ui.rb_voxel_disactive.toggled.connect(self.rb_voxel_active_clicked)
        self.ui.rb_presence_active.toggled.connect(self.rb_presence_active_clicked)
        self.ui.rb_presence_disactive.toggled.connect(self.rb_presence_active_clicked)
        self.ui.rb_stlle_plate_active.toggled.connect(self.rb_stlle_plate_active_clicked)
        self.ui.rb_stlle_plate_disactive.toggled.connect(self.rb_stlle_plate_active_clicked)
        self.ui.rb_related_samples_active.toggled.connect(self.rb_related_samples_clicked)
        self.ui.rb_related_samples_disactive.toggled.connect(self.rb_related_samples_clicked)

        self.ui.rb_grinding_1.toggled.connect(self.rb_diamond_bite_cliked)
        self.ui.rb_grinding_2.toggled.connect(self.rb_diamond_bite_cliked)
        self.ui.e_digital_specimen_number.textChanged.connect(self.change_dsn)

        self.ui.sp_animation_num.valueChanged.connect(self.sp_animation)

        #撮影条件一覧
        self.all_lane_numbers = [self.ui.cb_lane_1,self.ui.cb_lane_2,self.ui.cb_lane_3,self.ui.cb_lane_4,self.ui.cb_lane_5,self.ui.cb_lane_6,self.ui.cb_lane_7,self.ui.cb_lane_8,self.ui.cb_lane_9,self.ui.cb_lane_10,
                        self.ui.cb_lane_11,self.ui.cb_lane_12,self.ui.cb_lane_13,self.ui.cb_lane_14,self.ui.cb_lane_15,self.ui.cb_lane_16,self.ui.cb_lane_17,self.ui.cb_lane_18,self.ui.cb_lane_19,self.ui.cb_lane_20,
                        self.ui.cb_lane_21,self.ui.cb_lane_22,self.ui.cb_lane_23,self.ui.cb_lane_24,self.ui.cb_lane_25,self.ui.cb_lane_26,self.ui.cb_lane_27,self.ui.cb_lane_28,self.ui.cb_lane_29,self.ui.cb_lane_30,
                        self.ui.cb_lane_31,self.ui.cb_lane_32,self.ui.cb_lane_33,self.ui.cb_lane_34,self.ui.cb_lane_35,self.ui.cb_lane_36,self.ui.cb_lane_37,self.ui.cb_lane_38,self.ui.cb_lane_39,self.ui.cb_lane_40,
                        self.ui.cb_lane_41,self.ui.cb_lane_42,self.ui.cb_lane_43,self.ui.cb_lane_44,self.ui.cb_lane_45,self.ui.cb_lane_46,self.ui.cb_lane_47,self.ui.cb_lane_48,self.ui.cb_lane_49,self.ui.cb_lane_50,
                        self.ui.cb_lane_51,self.ui.cb_lane_52,self.ui.cb_lane_53,self.ui.cb_lane_54,self.ui.cb_lane_55,self.ui.cb_lane_56,self.ui.cb_lane_57,self.ui.cb_lane_58,self.ui.cb_lane_59,self.ui.cb_lane_60,
                        self.ui.cb_lane_61,self.ui.cb_lane_62,self.ui.cb_lane_63,self.ui.cb_lane_64,self.ui.cb_lane_65,self.ui.cb_lane_66,self.ui.cb_lane_67,self.ui.cb_lane_68,self.ui.cb_lane_69,self.ui.cb_lane_70,
                        self.ui.cb_lane_71,self.ui.cb_lane_72,self.ui.cb_lane_73,self.ui.cb_lane_74,self.ui.cb_lane_75,self.ui.cb_lane_76,self.ui.cb_lane_77,self.ui.cb_lane_78,self.ui.cb_lane_79,self.ui.cb_lane_80,
                        self.ui.cb_lane_81,self.ui.cb_lane_82,self.ui.cb_lane_83,self.ui.cb_lane_84,self.ui.cb_lane_85,self.ui.cb_lane_86,self.ui.cb_lane_87,self.ui.cb_lane_88,self.ui.cb_lane_89,self.ui.cb_lane_90,
                        self.ui.cb_lane_91,self.ui.cb_lane_92,self.ui.cb_lane_93,self.ui.cb_lane_94,self.ui.cb_lane_95,self.ui.cb_lane_96,self.ui.cb_lane_97,self.ui.cb_lane_98,self.ui.cb_lane_99,self.ui.cb_lane_100,
                        self.ui.cb_lane_101,self.ui.cb_lane_102,self.ui.cb_lane_103,self.ui.cb_lane_104,self.ui.cb_lane_105,self.ui.cb_lane_106,self.ui.cb_lane_107,self.ui.cb_lane_108,self.ui.cb_lane_109,self.ui.cb_lane_110,
                        self.ui.cb_lane_111,self.ui.cb_lane_112,self.ui.cb_lane_113,self.ui.cb_lane_114,self.ui.cb_lane_115,self.ui.cb_lane_116,self.ui.cb_lane_117,self.ui.cb_lane_118,self.ui.cb_lane_119,self.ui.cb_lane_120]

        self.e_lights = [self.ui.e_light_1,self.ui.e_light_2,self.ui.e_light_3,self.ui.e_light_4,self.ui.e_light_5,self.ui.e_light_6,self.ui.e_light_7,self.ui.e_light_8,self.ui.e_light_9,self.ui.e_light_10,
                        self.ui.e_light_11,self.ui.e_light_12,self.ui.e_light_13,self.ui.e_light_14,self.ui.e_light_15,self.ui.e_light_16,self.ui.e_light_17,self.ui.e_light_18,self.ui.e_light_19,self.ui.e_light_20,
                        self.ui.e_light_21,self.ui.e_light_22,self.ui.e_light_23,self.ui.e_light_24,self.ui.e_light_25,self.ui.e_light_26,self.ui.e_light_27,self.ui.e_light_28,self.ui.e_light_29,self.ui.e_light_30,
                        self.ui.e_light_31,self.ui.e_light_32,self.ui.e_light_33,self.ui.e_light_34,self.ui.e_light_35,self.ui.e_light_36,self.ui.e_light_37,self.ui.e_light_38,self.ui.e_light_39,self.ui.e_light_40,
                        self.ui.e_light_41,self.ui.e_light_42,self.ui.e_light_43,self.ui.e_light_44,self.ui.e_light_45,self.ui.e_light_46,self.ui.e_light_47,self.ui.e_light_48,self.ui.e_light_49,self.ui.e_light_50,
                        self.ui.e_light_51,self.ui.e_light_52,self.ui.e_light_53,self.ui.e_light_54,self.ui.e_light_55,self.ui.e_light_56,self.ui.e_light_57,self.ui.e_light_58,self.ui.e_light_59,self.ui.e_light_60,
                        self.ui.e_light_61,self.ui.e_light_62,self.ui.e_light_63,self.ui.e_light_64,self.ui.e_light_65,self.ui.e_light_66,self.ui.e_light_67,self.ui.e_light_68,self.ui.e_light_69,self.ui.e_light_70,
                        self.ui.e_light_71,self.ui.e_light_72,self.ui.e_light_73,self.ui.e_light_74,self.ui.e_light_75,self.ui.e_light_76,self.ui.e_light_77,self.ui.e_light_78,self.ui.e_light_79,self.ui.e_light_80,
                        self.ui.e_light_81,self.ui.e_light_82,self.ui.e_light_83,self.ui.e_light_84,self.ui.e_light_85,self.ui.e_light_86,self.ui.e_light_87,self.ui.e_light_88,self.ui.e_light_89,self.ui.e_light_90,
                        self.ui.e_light_91,self.ui.e_light_92,self.ui.e_light_93,self.ui.e_light_94,self.ui.e_light_95,self.ui.e_light_96,self.ui.e_light_97,self.ui.e_light_98,self.ui.e_light_99,self.ui.e_light_100,
                        self.ui.e_light_101,self.ui.e_light_102,self.ui.e_light_103,self.ui.e_light_104,self.ui.e_light_105,self.ui.e_light_106,self.ui.e_light_107,self.ui.e_light_108,self.ui.e_light_109,self.ui.e_light_110,
                        self.ui.e_light_111,self.ui.e_light_112,self.ui.e_light_113,self.ui.e_light_114,self.ui.e_light_115,self.ui.e_light_116,self.ui.e_light_117,self.ui.e_light_118,self.ui.e_light_119,self.ui.e_light_120]

        self.e_position_nos = [self.ui.e_position_no_1,self.ui.e_position_no_2,self.ui.e_position_no_3,self.ui.e_position_no_4,self.ui.e_position_no_5,self.ui.e_position_no_6,self.ui.e_position_no_7,self.ui.e_position_no_8,self.ui.e_position_no_9,self.ui.e_position_no_10,
                        self.ui.e_position_no_11,self.ui.e_position_no_12,self.ui.e_position_no_13,self.ui.e_position_no_14,self.ui.e_position_no_15,self.ui.e_position_no_16,self.ui.e_position_no_17,self.ui.e_position_no_18,self.ui.e_position_no_19,self.ui.e_position_no_20,
                        self.ui.e_position_no_21,self.ui.e_position_no_22,self.ui.e_position_no_23,self.ui.e_position_no_24,self.ui.e_position_no_25,self.ui.e_position_no_26,self.ui.e_position_no_27,self.ui.e_position_no_28,self.ui.e_position_no_29,self.ui.e_position_no_30,
                        self.ui.e_position_no_31,self.ui.e_position_no_32,self.ui.e_position_no_33,self.ui.e_position_no_34,self.ui.e_position_no_35,self.ui.e_position_no_36,self.ui.e_position_no_37,self.ui.e_position_no_38,self.ui.e_position_no_39,self.ui.e_position_no_40,
                        self.ui.e_position_no_41,self.ui.e_position_no_42,self.ui.e_position_no_43,self.ui.e_position_no_44,self.ui.e_position_no_45,self.ui.e_position_no_46,self.ui.e_position_no_47,self.ui.e_position_no_48,self.ui.e_position_no_49,self.ui.e_position_no_50,
                        self.ui.e_position_no_51,self.ui.e_position_no_52,self.ui.e_position_no_53,self.ui.e_position_no_54,self.ui.e_position_no_55,self.ui.e_position_no_56,self.ui.e_position_no_57,self.ui.e_position_no_58,self.ui.e_position_no_59,self.ui.e_position_no_60,
                        self.ui.e_position_no_61,self.ui.e_position_no_62,self.ui.e_position_no_63,self.ui.e_position_no_64,self.ui.e_position_no_65,self.ui.e_position_no_66,self.ui.e_position_no_67,self.ui.e_position_no_68,self.ui.e_position_no_69,self.ui.e_position_no_70,
                        self.ui.e_position_no_71,self.ui.e_position_no_72,self.ui.e_position_no_73,self.ui.e_position_no_74,self.ui.e_position_no_75,self.ui.e_position_no_76,self.ui.e_position_no_77,self.ui.e_position_no_78,self.ui.e_position_no_79,self.ui.e_position_no_80,
                        self.ui.e_position_no_81,self.ui.e_position_no_82,self.ui.e_position_no_83,self.ui.e_position_no_84,self.ui.e_position_no_85,self.ui.e_position_no_86,self.ui.e_position_no_87,self.ui.e_position_no_88,self.ui.e_position_no_89,self.ui.e_position_no_90,
                        self.ui.e_position_no_91,self.ui.e_position_no_92,self.ui.e_position_no_93,self.ui.e_position_no_94,self.ui.e_position_no_95,self.ui.e_position_no_96,self.ui.e_position_no_97,self.ui.e_position_no_98,self.ui.e_position_no_99,self.ui.e_position_no_100,
                        self.ui.e_position_no_101,self.ui.e_position_no_102,self.ui.e_position_no_103,self.ui.e_position_no_104,self.ui.e_position_no_105,self.ui.e_position_no_106,self.ui.e_position_no_107,self.ui.e_position_no_108,self.ui.e_position_no_109,self.ui.e_position_no_110,
                        self.ui.e_position_no_111,self.ui.e_position_no_112,self.ui.e_position_no_113,self.ui.e_position_no_114,self.ui.e_position_no_115,self.ui.e_position_no_116,self.ui.e_position_no_117,self.ui.e_position_no_118,self.ui.e_position_no_119,self.ui.e_position_no_120]
        
        self.e_corts = [self.ui.e_cort_1,self.ui.e_cort_2,self.ui.e_cort_3,self.ui.e_cort_4,self.ui.e_cort_5,self.ui.e_cort_6,self.ui.e_cort_7,self.ui.e_cort_8,self.ui.e_cort_9,self.ui.e_cort_10,
                        self.ui.e_cort_11,self.ui.e_cort_12,self.ui.e_cort_13,self.ui.e_cort_14,self.ui.e_cort_15,self.ui.e_cort_16,self.ui.e_cort_17,self.ui.e_cort_18,self.ui.e_cort_19,self.ui.e_cort_20,
                        self.ui.e_cort_21,self.ui.e_cort_22,self.ui.e_cort_23,self.ui.e_cort_24,self.ui.e_cort_25,self.ui.e_cort_26,self.ui.e_cort_27,self.ui.e_cort_28,self.ui.e_cort_29,self.ui.e_cort_30,
                        self.ui.e_cort_31,self.ui.e_cort_32,self.ui.e_cort_33,self.ui.e_cort_34,self.ui.e_cort_35,self.ui.e_cort_36,self.ui.e_cort_37,self.ui.e_cort_38,self.ui.e_cort_39,self.ui.e_cort_40,
                        self.ui.e_cort_41,self.ui.e_cort_42,self.ui.e_cort_43,self.ui.e_cort_44,self.ui.e_cort_45,self.ui.e_cort_46,self.ui.e_cort_47,self.ui.e_cort_48,self.ui.e_cort_49,self.ui.e_cort_50,
                        self.ui.e_cort_51,self.ui.e_cort_52,self.ui.e_cort_53,self.ui.e_cort_54,self.ui.e_cort_55,self.ui.e_cort_56,self.ui.e_cort_57,self.ui.e_cort_58,self.ui.e_cort_59,self.ui.e_cort_60,
                        self.ui.e_cort_61,self.ui.e_cort_62,self.ui.e_cort_63,self.ui.e_cort_64,self.ui.e_cort_65,self.ui.e_cort_66,self.ui.e_cort_67,self.ui.e_cort_68,self.ui.e_cort_69,self.ui.e_cort_70,
                        self.ui.e_cort_71,self.ui.e_cort_72,self.ui.e_cort_73,self.ui.e_cort_74,self.ui.e_cort_75,self.ui.e_cort_76,self.ui.e_cort_77,self.ui.e_cort_78,self.ui.e_cort_79,self.ui.e_cort_80,
                        self.ui.e_cort_81,self.ui.e_cort_82,self.ui.e_cort_83,self.ui.e_cort_84,self.ui.e_cort_85,self.ui.e_cort_86,self.ui.e_cort_87,self.ui.e_cort_88,self.ui.e_cort_89,self.ui.e_cort_90,
                        self.ui.e_cort_91,self.ui.e_cort_92,self.ui.e_cort_93,self.ui.e_cort_94,self.ui.e_cort_95,self.ui.e_cort_96,self.ui.e_cort_97,self.ui.e_cort_98,self.ui.e_cort_99,self.ui.e_cort_100,
                        self.ui.e_cort_101,self.ui.e_cort_102,self.ui.e_cort_103,self.ui.e_cort_104,self.ui.e_cort_105,self.ui.e_cort_106,self.ui.e_cort_107,self.ui.e_cort_108,self.ui.e_cort_109,self.ui.e_cort_110,
                        self.ui.e_cort_111,self.ui.e_cort_112,self.ui.e_cort_113,self.ui.e_cort_114,self.ui.e_cort_115,self.ui.e_cort_116,self.ui.e_cort_117,self.ui.e_cort_118,self.ui.e_cort_119,self.ui.e_cort_120]
        
        self.e_blows = [self.ui.e_blow_1,self.ui.e_blow_2,self.ui.e_blow_3,self.ui.e_blow_4,self.ui.e_blow_5,self.ui.e_blow_6,self.ui.e_blow_7,self.ui.e_blow_8,self.ui.e_blow_9,self.ui.e_blow_10,
                        self.ui.e_blow_11,self.ui.e_blow_12,self.ui.e_blow_13,self.ui.e_blow_14,self.ui.e_blow_15,self.ui.e_blow_16,self.ui.e_blow_17,self.ui.e_blow_18,self.ui.e_blow_19,self.ui.e_blow_20,
                        self.ui.e_blow_21,self.ui.e_blow_22,self.ui.e_blow_23,self.ui.e_blow_24,self.ui.e_blow_25,self.ui.e_blow_26,self.ui.e_blow_27,self.ui.e_blow_28,self.ui.e_blow_29,self.ui.e_blow_30,
                        self.ui.e_blow_31,self.ui.e_blow_32,self.ui.e_blow_33,self.ui.e_blow_34,self.ui.e_blow_35,self.ui.e_blow_36,self.ui.e_blow_37,self.ui.e_blow_38,self.ui.e_blow_39,self.ui.e_blow_40,
                        self.ui.e_blow_41,self.ui.e_blow_42,self.ui.e_blow_43,self.ui.e_blow_44,self.ui.e_blow_45,self.ui.e_blow_46,self.ui.e_blow_47,self.ui.e_blow_48,self.ui.e_blow_49,self.ui.e_blow_50,
                        self.ui.e_blow_51,self.ui.e_blow_52,self.ui.e_blow_53,self.ui.e_blow_54,self.ui.e_blow_55,self.ui.e_blow_56,self.ui.e_blow_57,self.ui.e_blow_58,self.ui.e_blow_59,self.ui.e_blow_60,
                        self.ui.e_blow_61,self.ui.e_blow_62,self.ui.e_blow_63,self.ui.e_blow_64,self.ui.e_blow_65,self.ui.e_blow_66,self.ui.e_blow_67,self.ui.e_blow_68,self.ui.e_blow_69,self.ui.e_blow_70,
                        self.ui.e_blow_71,self.ui.e_blow_72,self.ui.e_blow_73,self.ui.e_blow_74,self.ui.e_blow_75,self.ui.e_blow_76,self.ui.e_blow_77,self.ui.e_blow_78,self.ui.e_blow_79,self.ui.e_blow_80,
                        self.ui.e_blow_81,self.ui.e_blow_82,self.ui.e_blow_83,self.ui.e_blow_84,self.ui.e_blow_85,self.ui.e_blow_86,self.ui.e_blow_87,self.ui.e_blow_88,self.ui.e_blow_89,self.ui.e_blow_90,
                        self.ui.e_blow_91,self.ui.e_blow_92,self.ui.e_blow_93,self.ui.e_blow_94,self.ui.e_blow_95,self.ui.e_blow_96,self.ui.e_blow_97,self.ui.e_blow_98,self.ui.e_blow_99,self.ui.e_blow_100,
                        self.ui.e_blow_101,self.ui.e_blow_102,self.ui.e_blow_103,self.ui.e_blow_104,self.ui.e_blow_105,self.ui.e_blow_106,self.ui.e_blow_107,self.ui.e_blow_108,self.ui.e_blow_109,self.ui.e_blow_110,
                        self.ui.e_blow_111,self.ui.e_blow_112,self.ui.e_blow_113,self.ui.e_blow_114,self.ui.e_blow_115,self.ui.e_blow_116,self.ui.e_blow_117,self.ui.e_blow_118,self.ui.e_blow_119,self.ui.e_blow_120]
        
        self.e_frequencys = [self.ui.e_frequency_1,self.ui.e_frequency_2,self.ui.e_frequency_3,self.ui.e_frequency_4,self.ui.e_frequency_5,self.ui.e_frequency_6,self.ui.e_frequency_7,self.ui.e_frequency_8,self.ui.e_frequency_9,self.ui.e_frequency_10,
                        self.ui.e_frequency_11,self.ui.e_frequency_12,self.ui.e_frequency_13,self.ui.e_frequency_14,self.ui.e_frequency_15,self.ui.e_frequency_16,self.ui.e_frequency_17,self.ui.e_frequency_18,self.ui.e_frequency_19,self.ui.e_frequency_20,
                        self.ui.e_frequency_21,self.ui.e_frequency_22,self.ui.e_frequency_23,self.ui.e_frequency_24,self.ui.e_frequency_25,self.ui.e_frequency_26,self.ui.e_frequency_27,self.ui.e_frequency_28,self.ui.e_frequency_29,self.ui.e_frequency_30,
                        self.ui.e_frequency_31,self.ui.e_frequency_32,self.ui.e_frequency_33,self.ui.e_frequency_34,self.ui.e_frequency_35,self.ui.e_frequency_36,self.ui.e_frequency_37,self.ui.e_frequency_38,self.ui.e_frequency_39,self.ui.e_frequency_40,
                        self.ui.e_frequency_41,self.ui.e_frequency_42,self.ui.e_frequency_43,self.ui.e_frequency_44,self.ui.e_frequency_45,self.ui.e_frequency_46,self.ui.e_frequency_47,self.ui.e_frequency_48,self.ui.e_frequency_49,self.ui.e_frequency_50,
                        self.ui.e_frequency_51,self.ui.e_frequency_52,self.ui.e_frequency_53,self.ui.e_frequency_54,self.ui.e_frequency_55,self.ui.e_frequency_56,self.ui.e_frequency_57,self.ui.e_frequency_58,self.ui.e_frequency_59,self.ui.e_frequency_60,
                        self.ui.e_frequency_61,self.ui.e_frequency_62,self.ui.e_frequency_63,self.ui.e_frequency_64,self.ui.e_frequency_65,self.ui.e_frequency_66,self.ui.e_frequency_67,self.ui.e_frequency_68,self.ui.e_frequency_69,self.ui.e_frequency_70,
                        self.ui.e_frequency_71,self.ui.e_frequency_72,self.ui.e_frequency_73,self.ui.e_frequency_74,self.ui.e_frequency_75,self.ui.e_frequency_76,self.ui.e_frequency_77,self.ui.e_frequency_78,self.ui.e_frequency_79,self.ui.e_frequency_80,
                        self.ui.e_frequency_81,self.ui.e_frequency_82,self.ui.e_frequency_83,self.ui.e_frequency_84,self.ui.e_frequency_85,self.ui.e_frequency_86,self.ui.e_frequency_87,self.ui.e_frequency_88,self.ui.e_frequency_89,self.ui.e_frequency_90,
                        self.ui.e_frequency_91,self.ui.e_frequency_92,self.ui.e_frequency_93,self.ui.e_frequency_94,self.ui.e_frequency_95,self.ui.e_frequency_96,self.ui.e_frequency_97,self.ui.e_frequency_98,self.ui.e_frequency_99,self.ui.e_frequency_100,
                        self.ui.e_frequency_100,self.ui.e_frequency_102,self.ui.e_frequency_103,self.ui.e_frequency_104,self.ui.e_frequency_105,self.ui.e_frequency_106,self.ui.e_frequency_107,self.ui.e_frequency_108,self.ui.e_frequency_109,self.ui.e_frequency_110,
                        self.ui.e_frequency_110,self.ui.e_frequency_112,self.ui.e_frequency_113,self.ui.e_frequency_114,self.ui.e_frequency_115,self.ui.e_frequency_116,self.ui.e_frequency_117,self.ui.e_frequency_118,self.ui.e_frequency_119,self.ui.e_frequency_120]
        
        self.e_photographing_signals = [self.ui.e_photographing_signals_1,self.ui.e_photographing_signals_2,self.ui.e_photographing_signals_3,self.ui.e_photographing_signals_4,self.ui.e_photographing_signals_5,self.ui.e_photographing_signals_6,self.ui.e_photographing_signals_7,self.ui.e_photographing_signals_8,self.ui.e_photographing_signals_9,self.ui.e_photographing_signals_10,
                        self.ui.e_photographing_signals_11,self.ui.e_photographing_signals_12,self.ui.e_photographing_signals_13,self.ui.e_photographing_signals_14,self.ui.e_photographing_signals_15,self.ui.e_photographing_signals_16,self.ui.e_photographing_signals_17,self.ui.e_photographing_signals_18,self.ui.e_photographing_signals_19,self.ui.e_photographing_signals_20,
                        self.ui.e_photographing_signals_21,self.ui.e_photographing_signals_22,self.ui.e_photographing_signals_23,self.ui.e_photographing_signals_24,self.ui.e_photographing_signals_25,self.ui.e_photographing_signals_26,self.ui.e_photographing_signals_27,self.ui.e_photographing_signals_28,self.ui.e_photographing_signals_29,self.ui.e_photographing_signals_30,
                        self.ui.e_photographing_signals_31,self.ui.e_photographing_signals_32,self.ui.e_photographing_signals_33,self.ui.e_photographing_signals_34,self.ui.e_photographing_signals_35,self.ui.e_photographing_signals_36,self.ui.e_photographing_signals_37,self.ui.e_photographing_signals_38,self.ui.e_photographing_signals_39,self.ui.e_photographing_signals_40,
                        self.ui.e_photographing_signals_41,self.ui.e_photographing_signals_42,self.ui.e_photographing_signals_43,self.ui.e_photographing_signals_44,self.ui.e_photographing_signals_45,self.ui.e_photographing_signals_46,self.ui.e_photographing_signals_47,self.ui.e_photographing_signals_48,self.ui.e_photographing_signals_49,self.ui.e_photographing_signals_50,
                        self.ui.e_photographing_signals_51,self.ui.e_photographing_signals_52,self.ui.e_photographing_signals_53,self.ui.e_photographing_signals_54,self.ui.e_photographing_signals_55,self.ui.e_photographing_signals_56,self.ui.e_photographing_signals_57,self.ui.e_photographing_signals_58,self.ui.e_photographing_signals_59,self.ui.e_photographing_signals_60,
                        self.ui.e_photographing_signals_61,self.ui.e_photographing_signals_62,self.ui.e_photographing_signals_63,self.ui.e_photographing_signals_64,self.ui.e_photographing_signals_65,self.ui.e_photographing_signals_66,self.ui.e_photographing_signals_67,self.ui.e_photographing_signals_68,self.ui.e_photographing_signals_69,self.ui.e_photographing_signals_70,
                        self.ui.e_photographing_signals_71,self.ui.e_photographing_signals_72,self.ui.e_photographing_signals_73,self.ui.e_photographing_signals_74,self.ui.e_photographing_signals_75,self.ui.e_photographing_signals_76,self.ui.e_photographing_signals_77,self.ui.e_photographing_signals_78,self.ui.e_photographing_signals_79,self.ui.e_photographing_signals_80,
                        self.ui.e_photographing_signals_81,self.ui.e_photographing_signals_82,self.ui.e_photographing_signals_83,self.ui.e_photographing_signals_84,self.ui.e_photographing_signals_85,self.ui.e_photographing_signals_86,self.ui.e_photographing_signals_87,self.ui.e_photographing_signals_88,self.ui.e_photographing_signals_89,self.ui.e_photographing_signals_90,
                        self.ui.e_photographing_signals_91,self.ui.e_photographing_signals_92,self.ui.e_photographing_signals_93,self.ui.e_photographing_signals_94,self.ui.e_photographing_signals_95,self.ui.e_photographing_signals_96,self.ui.e_photographing_signals_97,self.ui.e_photographing_signals_98,self.ui.e_photographing_signals_99,self.ui.e_photographing_signals_100,
                        self.ui.e_photographing_signals_100,self.ui.e_photographing_signals_102,self.ui.e_photographing_signals_103,self.ui.e_photographing_signals_104,self.ui.e_photographing_signals_105,self.ui.e_photographing_signals_106,self.ui.e_photographing_signals_107,self.ui.e_photographing_signals_108,self.ui.e_photographing_signals_109,self.ui.e_photographing_signals_110,
                        self.ui.e_photographing_signals_110,self.ui.e_photographing_signals_112,self.ui.e_photographing_signals_113,self.ui.e_photographing_signals_114,self.ui.e_photographing_signals_115,self.ui.e_photographing_signals_116,self.ui.e_photographing_signals_117,self.ui.e_photographing_signals_118,self.ui.e_photographing_signals_119,self.ui.e_photographing_signals_120]
        
        self.e_wating_time_bs = [self.ui.e_wating_time_b_1,self.ui.e_wating_time_b_2,self.ui.e_wating_time_b_3,self.ui.e_wating_time_b_4,self.ui.e_wating_time_b_5,self.ui.e_wating_time_b_6,self.ui.e_wating_time_b_7,self.ui.e_wating_time_b_8,self.ui.e_wating_time_b_9,self.ui.e_wating_time_b_10,
                        self.ui.e_wating_time_b_11,self.ui.e_wating_time_b_12,self.ui.e_wating_time_b_13,self.ui.e_wating_time_b_14,self.ui.e_wating_time_b_15,self.ui.e_wating_time_b_16,self.ui.e_wating_time_b_17,self.ui.e_wating_time_b_18,self.ui.e_wating_time_b_19,self.ui.e_wating_time_b_20,
                        self.ui.e_wating_time_b_21,self.ui.e_wating_time_b_22,self.ui.e_wating_time_b_23,self.ui.e_wating_time_b_24,self.ui.e_wating_time_b_25,self.ui.e_wating_time_b_26,self.ui.e_wating_time_b_27,self.ui.e_wating_time_b_28,self.ui.e_wating_time_b_29,self.ui.e_wating_time_b_30,
                        self.ui.e_wating_time_b_31,self.ui.e_wating_time_b_32,self.ui.e_wating_time_b_33,self.ui.e_wating_time_b_34,self.ui.e_wating_time_b_35,self.ui.e_wating_time_b_36,self.ui.e_wating_time_b_37,self.ui.e_wating_time_b_38,self.ui.e_wating_time_b_39,self.ui.e_wating_time_b_40,
                        self.ui.e_wating_time_b_41,self.ui.e_wating_time_b_42,self.ui.e_wating_time_b_43,self.ui.e_wating_time_b_44,self.ui.e_wating_time_b_45,self.ui.e_wating_time_b_46,self.ui.e_wating_time_b_47,self.ui.e_wating_time_b_48,self.ui.e_wating_time_b_49,self.ui.e_wating_time_b_50,
                        self.ui.e_wating_time_b_51,self.ui.e_wating_time_b_52,self.ui.e_wating_time_b_53,self.ui.e_wating_time_b_54,self.ui.e_wating_time_b_55,self.ui.e_wating_time_b_56,self.ui.e_wating_time_b_57,self.ui.e_wating_time_b_58,self.ui.e_wating_time_b_59,self.ui.e_wating_time_b_60,
                        self.ui.e_wating_time_b_61,self.ui.e_wating_time_b_62,self.ui.e_wating_time_b_63,self.ui.e_wating_time_b_64,self.ui.e_wating_time_b_65,self.ui.e_wating_time_b_66,self.ui.e_wating_time_b_67,self.ui.e_wating_time_b_68,self.ui.e_wating_time_b_69,self.ui.e_wating_time_b_70,
                        self.ui.e_wating_time_b_71,self.ui.e_wating_time_b_72,self.ui.e_wating_time_b_73,self.ui.e_wating_time_b_74,self.ui.e_wating_time_b_75,self.ui.e_wating_time_b_76,self.ui.e_wating_time_b_77,self.ui.e_wating_time_b_78,self.ui.e_wating_time_b_79,self.ui.e_wating_time_b_80,
                        self.ui.e_wating_time_b_81,self.ui.e_wating_time_b_82,self.ui.e_wating_time_b_83,self.ui.e_wating_time_b_84,self.ui.e_wating_time_b_85,self.ui.e_wating_time_b_86,self.ui.e_wating_time_b_87,self.ui.e_wating_time_b_88,self.ui.e_wating_time_b_89,self.ui.e_wating_time_b_90,
                        self.ui.e_wating_time_b_91,self.ui.e_wating_time_b_92,self.ui.e_wating_time_b_93,self.ui.e_wating_time_b_94,self.ui.e_wating_time_b_95,self.ui.e_wating_time_b_96,self.ui.e_wating_time_b_97,self.ui.e_wating_time_b_98,self.ui.e_wating_time_b_99,self.ui.e_wating_time_b_100,
                        self.ui.e_wating_time_b_100,self.ui.e_wating_time_b_102,self.ui.e_wating_time_b_103,self.ui.e_wating_time_b_104,self.ui.e_wating_time_b_105,self.ui.e_wating_time_b_106,self.ui.e_wating_time_b_107,self.ui.e_wating_time_b_108,self.ui.e_wating_time_b_109,self.ui.e_wating_time_b_110,
                        self.ui.e_wating_time_b_110,self.ui.e_wating_time_b_112,self.ui.e_wating_time_b_113,self.ui.e_wating_time_b_114,self.ui.e_wating_time_b_115,self.ui.e_wating_time_b_116,self.ui.e_wating_time_b_117,self.ui.e_wating_time_b_118,self.ui.e_wating_time_b_119,self.ui.e_wating_time_b_120]

        self.e_wating_time_as = [self.ui.e_wating_time_a_1,self.ui.e_wating_time_a_2,self.ui.e_wating_time_a_3,self.ui.e_wating_time_a_4,self.ui.e_wating_time_a_5,self.ui.e_wating_time_a_6,self.ui.e_wating_time_a_7,self.ui.e_wating_time_a_8,self.ui.e_wating_time_a_9,self.ui.e_wating_time_a_10,
                        self.ui.e_wating_time_a_11,self.ui.e_wating_time_a_12,self.ui.e_wating_time_a_13,self.ui.e_wating_time_a_14,self.ui.e_wating_time_a_15,self.ui.e_wating_time_a_16,self.ui.e_wating_time_a_17,self.ui.e_wating_time_a_18,self.ui.e_wating_time_a_19,self.ui.e_wating_time_a_20,
                        self.ui.e_wating_time_a_21,self.ui.e_wating_time_a_22,self.ui.e_wating_time_a_23,self.ui.e_wating_time_a_24,self.ui.e_wating_time_a_25,self.ui.e_wating_time_a_26,self.ui.e_wating_time_a_27,self.ui.e_wating_time_a_28,self.ui.e_wating_time_a_29,self.ui.e_wating_time_a_30,
                        self.ui.e_wating_time_a_31,self.ui.e_wating_time_a_32,self.ui.e_wating_time_a_33,self.ui.e_wating_time_a_34,self.ui.e_wating_time_a_35,self.ui.e_wating_time_a_36,self.ui.e_wating_time_a_37,self.ui.e_wating_time_a_38,self.ui.e_wating_time_a_39,self.ui.e_wating_time_a_40,
                        self.ui.e_wating_time_a_41,self.ui.e_wating_time_a_42,self.ui.e_wating_time_a_43,self.ui.e_wating_time_a_44,self.ui.e_wating_time_a_45,self.ui.e_wating_time_a_46,self.ui.e_wating_time_a_47,self.ui.e_wating_time_a_48,self.ui.e_wating_time_a_49,self.ui.e_wating_time_a_50,
                        self.ui.e_wating_time_a_51,self.ui.e_wating_time_a_52,self.ui.e_wating_time_a_53,self.ui.e_wating_time_a_54,self.ui.e_wating_time_a_55,self.ui.e_wating_time_a_56,self.ui.e_wating_time_a_57,self.ui.e_wating_time_a_58,self.ui.e_wating_time_a_59,self.ui.e_wating_time_a_60,
                        self.ui.e_wating_time_a_61,self.ui.e_wating_time_a_62,self.ui.e_wating_time_a_63,self.ui.e_wating_time_a_64,self.ui.e_wating_time_a_65,self.ui.e_wating_time_a_66,self.ui.e_wating_time_a_67,self.ui.e_wating_time_a_68,self.ui.e_wating_time_a_69,self.ui.e_wating_time_a_70,
                        self.ui.e_wating_time_a_71,self.ui.e_wating_time_a_72,self.ui.e_wating_time_a_73,self.ui.e_wating_time_a_74,self.ui.e_wating_time_a_75,self.ui.e_wating_time_a_76,self.ui.e_wating_time_a_77,self.ui.e_wating_time_a_78,self.ui.e_wating_time_a_79,self.ui.e_wating_time_a_80,
                        self.ui.e_wating_time_a_81,self.ui.e_wating_time_a_82,self.ui.e_wating_time_a_83,self.ui.e_wating_time_a_84,self.ui.e_wating_time_a_85,self.ui.e_wating_time_a_86,self.ui.e_wating_time_a_87,self.ui.e_wating_time_a_88,self.ui.e_wating_time_a_89,self.ui.e_wating_time_a_90,
                        self.ui.e_wating_time_a_91,self.ui.e_wating_time_a_92,self.ui.e_wating_time_a_93,self.ui.e_wating_time_a_94,self.ui.e_wating_time_a_95,self.ui.e_wating_time_a_96,self.ui.e_wating_time_a_97,self.ui.e_wating_time_a_98,self.ui.e_wating_time_a_99,self.ui.e_wating_time_a_100,
                        self.ui.e_wating_time_a_100,self.ui.e_wating_time_a_102,self.ui.e_wating_time_a_103,self.ui.e_wating_time_a_104,self.ui.e_wating_time_a_105,self.ui.e_wating_time_a_106,self.ui.e_wating_time_a_107,self.ui.e_wating_time_a_108,self.ui.e_wating_time_a_109,self.ui.e_wating_time_a_110,
                        self.ui.e_wating_time_a_110,self.ui.e_wating_time_a_112,self.ui.e_wating_time_a_113,self.ui.e_wating_time_a_114,self.ui.e_wating_time_a_115,self.ui.e_wating_time_a_116,self.ui.e_wating_time_a_117,self.ui.e_wating_time_a_118,self.ui.e_wating_time_a_119,self.ui.e_wating_time_a_120]

        self.photoraphing_positions = [self.ui.e_photoraphing_position_1,self.ui.e_photoraphing_position_2,self.ui.e_photoraphing_position_3,self.ui.e_photoraphing_position_4,self.ui.e_photoraphing_position_5,self.ui.e_photoraphing_position_6,self.ui.e_photoraphing_position_7,self.ui.e_photoraphing_position_8,self.ui.e_photoraphing_position_9,self.ui.e_photoraphing_position_10,
                        self.ui.e_photoraphing_position_11,self.ui.e_photoraphing_position_12,self.ui.e_photoraphing_position_13,self.ui.e_photoraphing_position_14,self.ui.e_photoraphing_position_15,self.ui.e_photoraphing_position_16,self.ui.e_photoraphing_position_17,self.ui.e_photoraphing_position_18,self.ui.e_photoraphing_position_19,self.ui.e_photoraphing_position_20,
                        self.ui.e_photoraphing_position_21,self.ui.e_photoraphing_position_22,self.ui.e_photoraphing_position_23,self.ui.e_photoraphing_position_24,self.ui.e_photoraphing_position_25,self.ui.e_photoraphing_position_26,self.ui.e_photoraphing_position_27,self.ui.e_photoraphing_position_28,self.ui.e_photoraphing_position_29,self.ui.e_photoraphing_position_30,
                        self.ui.e_photoraphing_position_31,self.ui.e_photoraphing_position_32,self.ui.e_photoraphing_position_33,self.ui.e_photoraphing_position_34,self.ui.e_photoraphing_position_35,self.ui.e_photoraphing_position_36,self.ui.e_photoraphing_position_37,self.ui.e_photoraphing_position_38,self.ui.e_photoraphing_position_39,self.ui.e_photoraphing_position_40,
                        self.ui.e_photoraphing_position_41,self.ui.e_photoraphing_position_42,self.ui.e_photoraphing_position_43,self.ui.e_photoraphing_position_44,self.ui.e_photoraphing_position_45,self.ui.e_photoraphing_position_46,self.ui.e_photoraphing_position_47,self.ui.e_photoraphing_position_48,self.ui.e_photoraphing_position_49,self.ui.e_photoraphing_position_50,
                        self.ui.e_photoraphing_position_51,self.ui.e_photoraphing_position_52,self.ui.e_photoraphing_position_53,self.ui.e_photoraphing_position_54,self.ui.e_photoraphing_position_55,self.ui.e_photoraphing_position_56,self.ui.e_photoraphing_position_57,self.ui.e_photoraphing_position_58,self.ui.e_photoraphing_position_59,self.ui.e_photoraphing_position_60]
        self.photoraphing_positions_label = [self.ui.l_photo_position_1,self.ui.l_photo_position_2,self.ui.l_photo_position_3,self.ui.l_photo_position_4,self.ui.l_photo_position_5,self.ui.l_photo_position_6,self.ui.l_photo_position_7,self.ui.l_photo_position_8,self.ui.l_photo_position_9,self.ui.l_photo_position_10,
                        self.ui.l_photo_position_11,self.ui.l_photo_position_12,self.ui.l_photo_position_13,self.ui.l_photo_position_14,self.ui.l_photo_position_15,self.ui.l_photo_position_16,self.ui.l_photo_position_17,self.ui.l_photo_position_18,self.ui.l_photo_position_19,self.ui.l_photo_position_20,
                        self.ui.l_photo_position_21,self.ui.l_photo_position_22,self.ui.l_photo_position_23,self.ui.l_photo_position_24,self.ui.l_photo_position_25,self.ui.l_photo_position_26,self.ui.l_photo_position_27,self.ui.l_photo_position_28,self.ui.l_photo_position_29,self.ui.l_photo_position_30,
                        self.ui.l_photo_position_31,self.ui.l_photo_position_32,self.ui.l_photo_position_33,self.ui.l_photo_position_34,self.ui.l_photo_position_35,self.ui.l_photo_position_36,self.ui.l_photo_position_37,self.ui.l_photo_position_38,self.ui.l_photo_position_39,self.ui.l_photo_position_40,
                        self.ui.l_photo_position_41,self.ui.l_photo_position_42,self.ui.l_photo_position_43,self.ui.l_photo_position_44,self.ui.l_photo_position_45,self.ui.l_photo_position_46,self.ui.l_photo_position_47,self.ui.l_photo_position_48,self.ui.l_photo_position_49,self.ui.l_photo_position_50,
                        self.ui.l_photo_position_51,self.ui.l_photo_position_52,self.ui.l_photo_position_53,self.ui.l_photo_position_54,self.ui.l_photo_position_55,self.ui.l_photo_position_56,self.ui.l_photo_position_57,self.ui.l_photo_position_58,self.ui.l_photo_position_59,self.ui.l_photo_position_60]
        

        for all_lane_number in self.all_lane_numbers:
            all_lane_number.currentIndexChanged.connect(self.shot_list_enable)
        self.ui.voxels = []

        for i in range(len(self.e_frequencys)):
            self.e_frequencys[i].textChanged.connect(self.calc_voxel)
        self.ui.e_total_grinding_thickness_in_each_cycle.textChanged.connect(self.calc_voxel)
        
        #ラジオボタン、試料種類の初期設定
        self.default_settings()

        #コンボボックスによる動作
        self.ui.comb_details_of_preparation.currentIndexChanged.connect(self.select_other)
        self.ui.comb_interval_of_psms.currentIndexChanged.connect(self.select_other)
        self.ui.comb_lens_adpter.currentIndexChanged.connect(self.select_other)
        self.ui.cb_other_filter.stateChanged.connect(self.select_other)
        self.ui.comb_camera_number.currentIndexChanged.connect(self.change_cam_num)
        self.ui.comb_pixel_shift_nulti_shooting.currentIndexChanged.connect(self.change_cam_num)
        self.ui.cmb_grinding_tools.currentIndexChanged.connect(self.disable_kugiri)




        #チェックボックスによる動作
        self.ui.cb_presence_3.stateChanged.connect(self.cb_presence3)
        self.ui.cb_prepared_or_not.stateChanged.connect(self.cb_prepared)
        
        self.cb_filters = [self.ui.cb_filter_0,self.ui.cb_filter_1,self.ui.cb_filter_2,self.ui.cb_filter_3,self.ui.cb_filter_4,self.ui.cb_filter_5,
                        self.ui.cb_filter_6,self.ui.cb_filter_7,self.ui.cb_filter_8,self.ui.cb_filter_9,self.ui.cb_filter_10]
        for i in range(len(self.cb_filters)):
            self.cb_filters[i].stateChanged.connect(self.cb_filter_list)

        #テキストエリアの削除
        self.ui.b_trash_1.clicked.connect(self.text_trash)
        self.ui.b_trash_2.clicked.connect(self.text_trash)

        #スケールレイアウト変更時の操作
        e_grids = [self.ui.e_grid_A_1,self.ui.e_grid_A_2,self.ui.e_grid_A_3,self.ui.e_grid_A_4,self.ui.e_grid_A_5,
                self.ui.e_grid_B_1,self.ui.e_grid_B_2,self.ui.e_grid_B_3,self.ui.e_grid_B_4,self.ui.e_grid_B_5]
        for i in range(len(e_grids)):
            e_grids[i].textChanged.connect(self.scale)

        #照明種類変更時の動作
        self.comb_optical_types = [[self.ui.comb_optical_type_1_1,self.ui.comb_optical_type_2_1,self.ui.comb_optical_type_3_1,self.ui.comb_optical_type_4_1,self.ui.comb_optical_type_5_1,self.ui.comb_optical_type_6_1,self.ui.comb_optical_type_7_1,self.ui.comb_optical_type_8_1],
        [self.ui.comb_optical_type_1_2,self.ui.comb_optical_type_2_2,self.ui.comb_optical_type_3_2,self.ui.comb_optical_type_4_2,self.ui.comb_optical_type_5_2,self.ui.comb_optical_type_6_2,self.ui.comb_optical_type_7_2,self.ui.comb_optical_type_8_2],
        [self.ui.comb_optical_type_1_3,self.ui.comb_optical_type_2_3,self.ui.comb_optical_type_3_3,self.ui.comb_optical_type_4_3,self.ui.comb_optical_type_5_3,self.ui.comb_optical_type_6_3,self.ui.comb_optical_type_7_3,self.ui.comb_optical_type_8_3],
        [self.ui.comb_optical_type_1_4,self.ui.comb_optical_type_2_4,self.ui.comb_optical_type_3_4,self.ui.comb_optical_type_4_4,self.ui.comb_optical_type_5_4,self.ui.comb_optical_type_6_4,self.ui.comb_optical_type_7_4,self.ui.comb_optical_type_8_4]]

        self.color_temperatuers = [[self.ui.e_color_temperatuer_1_1,self.ui.e_color_temperatuer_2_1,self.ui.e_color_temperatuer_3_1,self.ui.e_color_temperatuer_4_1,self.ui.e_color_temperatuer_5_1,self.ui.e_color_temperatuer_6_1,self.ui.e_color_temperatuer_7_1,self.ui.e_color_temperatuer_8_1],
        [self.ui.e_color_temperatuer_1_2,self.ui.e_color_temperatuer_2_2,self.ui.e_color_temperatuer_3_2,self.ui.e_color_temperatuer_4_2,self.ui.e_color_temperatuer_5_2,self.ui.e_color_temperatuer_6_2,self.ui.e_color_temperatuer_7_2,self.ui.e_color_temperatuer_8_2],
        [self.ui.e_color_temperatuer_1_3,self.ui.e_color_temperatuer_2_3,self.ui.e_color_temperatuer_3_3,self.ui.e_color_temperatuer_4_3,self.ui.e_color_temperatuer_5_3,self.ui.e_color_temperatuer_6_3,self.ui.e_color_temperatuer_7_3,self.ui.e_color_temperatuer_8_3],
        [self.ui.e_color_temperatuer_1_4,self.ui.e_color_temperatuer_2_4,self.ui.e_color_temperatuer_3_4,self.ui.e_color_temperatuer_4_4,self.ui.e_color_temperatuer_5_4,self.ui.e_color_temperatuer_6_4,self.ui.e_color_temperatuer_7_4,self.ui.e_color_temperatuer_8_4]]

        ###
        ###Keysmithページ
        ###
        self.innerWidget1 = Keysmith1Widget(self)
        self.ui.sa_keysmith_1.setWidget(self.innerWidget1)
        self.innerWidget1.SetImage()

        self.innerWidget2 = Keysmith1Widget(self)
        self.ui.sa_keysmith_2.setWidget(self.innerWidget2)
        self.innerWidget2.SetImage()

        self.ui.b_plus.clicked.connect(self.innerWidget1.SetImage)
        self.ui.b_plus.clicked.connect(self.innerWidget2.SetImage)

        self.ui.b_keysmith_input.clicked.connect(self.keysmith_setting_input)
        self.ui.b_keysmith_output.clicked.connect(self.keysmith_setting_output)

        for i in range(4):
            for j in range(8):
                self.comb_optical_types[i][j].currentIndexChanged.connect(self.digital_names)

        for i in range(4):
            for j in range(8):
                self.color_temperatuers[i][j].textChanged.connect(self.change_temperature)

        for i in range(len(self.e_lights)):
            self.e_lights[i].textChanged.connect(self.digital_names)
        
        for i in range(len(self.e_position_nos)):
            self.e_position_nos[i].textChanged.connect(self.digital_names)

        #カメラの横置き/縦おきについて
        self.ui.cb_camera_operation_horizonal.toggled.connect(self.scale_set_position)
        self.ui.cb_camera_operation_vertical.toggled.connect(self.scale_set_position)

        #その他プッシュボタン操作
        self.ui.b_table.clicked.connect(self.sub_win)
        self.ui.b_scrll.clicked.connect(self.show_cb)

        self.stop_flag = False
        self.show()

    def output_volume_setting_sei(self):
        dir_path = None
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        # ディレクリのみ選択可能なダイアログを表示(選択した値がdir_pathに入る)
        dir_path = QFileDialog.getExistingDirectory(self)
        if(dir_path):
            self.ui.l_output_volume_sei.setText(dir_path)
            self.textBrowser_output('[EVENT]「LTO(正)」が' + dir_path + "に設定されました。")
            
    def output_volume_setting_huku(self):
        dir_path = None
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        # ディレクリのみ選択可能なダイアログを表示(選択した値がdir_pathに入る)
        dir_path = QFileDialog.getExistingDirectory(self)
        if(dir_path):
            self.ui.l_output_volume_huku.setText(dir_path)
            self.textBrowser_output('[EVENT]「LTO(副)」が' + dir_path + "に設定されました。")
                 

    def input_volume_setting(self):
        dir_path = None
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        # ディレクリのみ選択可能なダイアログを表示(選択した値がdir_pathに入る)
        dir_path = QFileDialog.getExistingDirectory(self)
        if(dir_path):
            self.ui.l_input_volume.setText(dir_path)
            self.textBrowser_output('[EVENT]「Input」が' + dir_path + "に設定されました。")
            self.change_dsn()

    def output_volume_setting(self):
        dir_path = None
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        # ディレクリのみ選択可能なダイアログを表示(選択した値がdir_pathに入る)
        dir_path = QFileDialog.getExistingDirectory(self)
        if(dir_path):
            self.ui.l_output_volume.setText(dir_path)
            self.textBrowser_output('[EVENT]「Output」が' + dir_path + "に設定されました。")
            self.change_dsn()

    def output_volume_setting_reset(self):
        self.ui.l_output_volume.setText("未選択")
        self.textBrowser_output('[EVENT]「Output」がリセットされました')
            
        self.change_dsn()

    def tmp_volume_setting(self):
        dir_path = None
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        # ディレクリのみ選択可能なダイアログを表示(選択した値がdir_pathに入る)
        dir_path = QFileDialog.getExistingDirectory(self)
        if(dir_path):
            self.ui.l_tmp_volume.setText(dir_path)
            self.textBrowser_output('[EVENT]「tmp」が' + dir_path + "に設定されました。")
            
            self.change_dsn()

    def tmp_volume_setting_reset(self):
        self.ui.l_tmp_volume.setText("未選択")
        self.textBrowser_output('[EVENT]「tmp」がリセットされました')
        self.change_dsn()

    def keysmith_setting_input(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        dist_path = os.path.join(os.getcwd() , 'settings')
        fname = QFileDialog.getOpenFileName(self, 'Open file', dist_path , '*.ini')
        if (fname[0]!= ""):#ファイルを読み込めたら
            try:
                config = configparser.ConfigParser()
                config.read(fname[0])
                
                for i in range(len(self.innerWidget1.LneEdts)):
                    self.innerWidget1.LneEdts[i].setText(config['Keysmith1'][str(i + 1)])
                    self.innerWidget2.LneEdts[i].setText(config['Keysmith2'][str(i + 1)])
                self.ui.l_keysmith_limit_message.setText('設定を読み込みました。')
            except:
                self.ui.l_keysmith_limit_message.setText('Keysmithの設定が記載されていません。')




    def keysmith_setting_output(self):
        try:
            dist_path = os.path.join(os.getcwd() , 'settings')
            os.mkdir(dist_path)
        except:
            pass
    
        if(self.innerWidget1.LneEdts[0].text() == "") or (self.innerWidget2.LneEdts[0].text() == ""):            
            self.ui.l_keysmith_limit_message.setText('Keysmith URL1あるいは2が未記入です。')
        elif(len(self.innerWidget1.LneEdts) != len(self.innerWidget2.LneEdts)):
            self.ui.l_keysmith_limit_message.setText('Keysmith URL1と2の入力数が合いません。')
        else:
            now = datetime.datetime.now()
            fileName = os.path.join(os.getcwd() , 'settings','keysmith_url' + now.strftime('%Y%m%d_%H%M') + '.ini')
            
            config = configparser.ConfigParser()

            config['Keysmith1'] = {}
            config['Keysmith2'] = {}
            for i in range(len(self.innerWidget1.LneEdts)):
                config['Keysmith1'][str(i + 1)] = self.innerWidget1.LneEdts[i].text()
                config['Keysmith2'][str(i + 1)] = self.innerWidget2.LneEdts[i].text()

            with open(fileName, 'w') as file:
                config.write(file)

            self.textBrowser_output('[EVENT]KMのセッティングファイルを出力しました。')
            self.textBrowser_output('   [INFO]「' + fileName + '」を確認してください。')
            self.ui.l_keysmith_limit_message.setText('出力完了：keysmith_url' + now.strftime('%Y%m%d_%H%M') + '.ini')

    def shot_list_enable(self):
        self.active_lane_numbers = 0
        for i in range(len(self.all_lane_numbers)):
            if(self.all_lane_numbers[i].currentText() == ''):
                self.e_lights[i].setEnabled(False)
                self.e_position_nos[i].setEnabled(False)
                self.e_corts[i].setEnabled(False)
                self.e_blows[i].setEnabled(False)
                self.e_frequencys[i].setEnabled(False)
                self.e_photographing_signals[i].setEnabled(False)
                self.e_wating_time_bs[i].setEnabled(False)
                self.e_wating_time_as[i].setEnabled(False)
                
                self.e_lights[i].setText('')
                self.e_position_nos[i].setText('')
                self.e_corts[i].setText('')
                self.e_blows[i].setText('')
                self.e_frequencys[i].setText('')
                self.e_photographing_signals[i].setText('')
                self.e_wating_time_bs[i].setText('')
                self.e_wating_time_as[i].setText('')

            else:
                self.active_lane_numbers = self.active_lane_numbers + 1
                self.e_lights[i].setEnabled(True)
                self.e_position_nos[i].setEnabled(True)
                self.e_corts[i].setEnabled(True)
                self.e_blows[i].setEnabled(True)
                self.e_frequencys[i].setEnabled(True)
                self.e_photographing_signals[i].setEnabled(True)
                self.e_wating_time_bs[i].setEnabled(True)
                self.e_wating_time_as[i].setEnabled(True)

        self.change_dsn()

    def stop_loop(self):
        self.execAction.quit()
        self.execAction.end_flag = True
        self.textBrowser_output('[STOP MODE START]中断処理を開始します。')
        filename = CreateLog.MakeLogFile(self,self.rb_sample_type,self.grinding_tools,True,os.path.basename(self.execAction.target_files[0]))
        self.textBrowser_output('[STOP MODE END]中断処理を終了します。')
        self.textBrowser_output('------------------------------------------')

    def rb_input(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_nokosu_opt = radioBtn.text()
            if(self.rb_nokosu_opt == "FullSet"):
                self.ui.cb_write_meta_2.setDisabled(True)
                self.ui.cb_write_lab_2.setDisabled(True)
                self.ui.cb_write_arw_2.setDisabled(True)
                self.ui.cb_write_tif_2.setDisabled(True)
                self.ui.cb_write_animation_2.setDisabled(True)
                self.ui.cb_write_meta_2.setChecked(True)
                self.ui.cb_write_lab_2.setChecked(True)
                self.ui.cb_write_arw_2.setChecked(True)
                self.ui.cb_write_tif_2.setChecked(True)
                self.ui.cb_write_animation_2.setChecked(True)
            else:
                self.ui.cb_write_meta_2.setDisabled(False)
                self.ui.cb_write_lab_2.setDisabled(False)
                self.ui.cb_write_arw_2.setDisabled(False)
                self.ui.cb_write_tif_2.setDisabled(False)
                self.ui.cb_write_animation_2.setDisabled(False)


    def rb_animation(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_animation_opt = radioBtn.text()
            if(self.rb_animation_opt == "任意枚数で作成"):
                self.textBrowser_output('[EVENT]Amimation出力を「' + self.rb_animation_opt + "(" + str(self.ui.sp_animation_num.value()) + "枚)」に設定しました。")
                self.ui.sp_animation_num.setDisabled(False)
                self.ui.cb_write_animation.setDisabled(False)
                self.ui.cb_write_animation_2.setDisabled(False)
            elif(self.rb_animation_opt == "なし"):
                self.ui.sp_animation_num.setDisabled(True)
                self.ui.cb_write_animation.setDisabled(True)
                self.ui.cb_write_animation.setChecked(False)
                self.ui.cb_write_animation_2.setDisabled(True)
                self.ui.cb_write_animation_2.setChecked(False)
                self.textBrowser_output('[EVENT]Amimation出力を「' + self.rb_animation_opt + "」に設定しました。")
            else:
                self.ui.sp_animation_num.setDisabled(True)
                self.ui.cb_write_animation.setDisabled(False)
                self.ui.cb_write_animation_2.setDisabled(False)
                self.textBrowser_output('[EVENT]Amimation出力を「' + self.rb_animation_opt + "」に設定しました。")
            
    def rb_full_select(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_full_opt = radioBtn.text()
            if(self.rb_full_opt == "FullSet"):
                self.ui.cb_write_meta.setDisabled(True)
                self.ui.cb_write_lab.setDisabled(True)
                self.ui.cb_write_arw.setDisabled(True)
                self.ui.cb_write_tif.setDisabled(True)
                self.ui.cb_write_animation.setDisabled(True)
                self.ui.cb_write_meta.setChecked(True)
                self.ui.cb_write_lab.setChecked(True)
                self.ui.cb_write_arw.setChecked(True)
                self.ui.cb_write_tif.setChecked(True)
                self.ui.cb_write_animation.setChecked(True)
            else:
                self.ui.cb_write_meta.setDisabled(False)
                self.ui.cb_write_lab.setDisabled(False)
                self.ui.cb_write_arw.setDisabled(False)
                self.ui.cb_write_tif.setDisabled(False)
                self.ui.cb_write_animation.setDisabled(False)

    def rb_lto_number(self):
        if(self.ui.rb_lto_dev_num_sei_1.isChecked() == True):
            self.ui.rb_lto_dev_num_huku_0.setChecked(True)
        else:
            self.ui.rb_lto_dev_num_sei_0.setChecked(True)
            self.ui.rb_lto_dev_num_huku_1.setChecked(True)

    def rb_lto(self):
        radioBtn = self.sender()
        
        if radioBtn.isChecked():
            self.rb_lto_opt = radioBtn.text()
            self.textBrowser_output('[EVENT]LTO出力を「' + self.rb_lto_opt + "」に設定しました。")
            self.ui.b_output_volume_sei.setDisabled(False)
            self.ui.b_output_volume_huku.setDisabled(False)

            if(self.rb_lto_opt == "正のみ"):
                self.ui.l_output_volume_huku.setText("「正のみ」に設定されています。")
                self.ui.b_output_volume_huku.setDisabled(True)
                self.ui.rb_lto_dev_num_huku_0.setEnabled(False)
                self.ui.rb_lto_dev_num_huku_1.setEnabled(False)                
                if(self.ui.l_output_volume_sei.text() == "「LTOなし」に設定されています。"):
                    self.ui.l_output_volume_sei.setText("未選択")

            elif(self.rb_lto_opt == "LTOなし"):
                self.ui.l_output_volume_sei.setText("「LTOなし」に設定されています。")
                self.ui.b_output_volume_sei.setDisabled(True)
                self.ui.l_output_volume_huku.setText("「LTOなし」に設定されています。")
                self.ui.b_output_volume_huku.setDisabled(True)
                self.ui.rb_lto_dev_num_sei_0.setEnabled(False)
                self.ui.rb_lto_dev_num_sei_1.setEnabled(False)
                self.ui.rb_lto_dev_num_huku_0.setEnabled(False)
                self.ui.rb_lto_dev_num_huku_1.setEnabled(False)

            else:
                if(self.ui.l_output_volume_sei.text() == "「LTOなし」に設定されています。"):
                    self.ui.l_output_volume_sei.setText("未選択")
                if(self.ui.l_output_volume_huku.text() == "「LTOなし」に設定されています。") or (self.ui.l_output_volume_huku.text() == "「正のみ」に設定されています。"):
                    self.ui.l_output_volume_huku.setText("未選択")
                    
                self.ui.rb_lto_dev_num_sei_0.setEnabled(True)
                self.ui.rb_lto_dev_num_sei_1.setEnabled(True)
                self.ui.rb_lto_dev_num_huku_0.setEnabled(True)
                self.ui.rb_lto_dev_num_huku_1.setEnabled(True)

                if(self.ui.rb_lto_dev_num_sei_1.isChecked() == True):
                    self.ui.rb_lto_dev_num_huku_0.setChecked(True)
                else:
                    self.ui.rb_lto_dev_num_sei_0.setChecked(True)
                    self.ui.rb_lto_dev_num_huku_1.setChecked(True)

                    


    def sp_animation(self):
        self.textBrowser_output('[EVENT]Amimation出力を「' + self.rb_animation_opt + "(" + str(self.ui.sp_animation_num.value()) + "枚)」に設定しました。")


    def show_cb(self):
        if(self.ui.b_scrll.text() == '+'):
            self.ui.scrl_cb_area.show()
            self.ui.b_scrll.setText('-')
        else:
            self.ui.scrl_cb_area.hide()
            self.ui.b_scrll.setText('+')
    
    def cb_filter_list(self):
        self.select_filters = []
        for i in range(len(self.cb_filters)):
            if(self.cb_filters[i].checkState() != 0):
                self.select_filters.append(self.cb_filters[i].text())


    def contents_able(self):
        self.ui.b_stop.setEnabled(True)
        self.ui.b_pause.setEnabled(True)
        #self.ui.b_log_output.setEnabled(True)

    def contents_disable(self):
        self.ui.b_import.setEnabled(False)
        self.ui.b_export.setEnabled(False)

        self.ui.e_digital_specimen_number.setEnabled(False)
        self.ui.e_date_of_analys.setEnabled(False)
        self.ui.e_analyst.setEnabled(False)
        self.ui.e_chatwork_api_key.setEnabled(False)
        self.ui.e_chatwork_room_id.setEnabled(False)
        self.ui.cb_same_time_mode.setEnabled(False)

        self.ui.rb_rock_sample.setEnabled(False)
        self.ui.rb_bioligical_sample.setEnabled(False)
        self.ui.rb_other_sample.setEnabled(False)
        self.ui.e_laboratory_identificiation_number.setEnabled(False)
        self.ui.e_puglic_collection_number_before_destructive_analysis.setEnabled(False)
        self.ui.e_taxon_lithology.setEnabled(False)
        self.ui.e_geological_age.setEnabled(False)
        self.ui.e_horizon.setEnabled(False)
        self.ui.e_locality.setEnabled(False)
        self.ui.e_latitude.setEnabled(False)
        self.ui.e_longitude.setEnabled(False)
        self.ui.e_time_and_date_of_collection.setEnabled(False)
        self.ui.e_age.setEnabled(False)
        self.ui.e_sex.setEnabled(False)
        self.ui.e_strage_condition.setEnabled(False)
        self.ui.e_sample_provider.setEnabled(False)
        self.ui.e_references.setEnabled(False)
        self.ui.cb_presence_3.setEnabled(False)
        self.ui.e_file_name.setEnabled(False)
        self.ui.e_size_of_sample.setEnabled(False)
        self.ui.cb_prepared_or_not.setEnabled(False)
        self.ui.comb_details_of_preparation.setEnabled(False)
        self.ui.e_other_preparation.setEnabled(False)
        self.ui.comb_aluminium_powder.setEnabled(False)
        self.ui.e_size_of_prepared_sample.setEnabled(False)
        self.ui.e_weight_of_sample.setEnabled(False)
        self.ui.e_weight_of_prepared_sample.setEnabled(False)

        #
        self.ui.b_input_volume.setEnabled(False)
        self.ui.b_output_volume.setEnabled(False)
        self.ui.b_tmp_volume.setEnabled(False)
        self.ui.b_output_volume_reset.setEnabled(False)
        self.ui.b_tmp_volume_reset.setEnabled(False)
        self.ui.b_output_volume_sei.setEnabled(False)
        self.ui.b_output_volume_huku.setEnabled(False)

        #
        
        self.ui.rb_lto_dev_num_sei_0.setEnabled(False)
        self.ui.rb_lto_dev_num_sei_1.setEnabled(False)
        self.ui.rb_lto_dev_num_huku_0.setEnabled(False)
        self.ui.rb_lto_dev_num_huku_1.setEnabled(False)
        self.ui.rb_animation_no.setEnabled(False)
        self.ui.rb_animation_all.setEnabled(False)
        self.ui.rb_animation_num.setEnabled(False)
        self.ui.sp_animation_num.setEnabled(False)

        #
        self.ui.rb_sei.setEnabled(False)
        self.ui.rb_seifuku.setEnabled(False)
        self.ui.rb_seifuku_nashi.setEnabled(False)
        self.ui.rb_full.setEnabled(False)
        self.ui.rb_nofull.setEnabled(False)
        self.ui.rb_nokosu.setEnabled(False)
        self.ui.rb_nokosanai.setEnabled(False)

        #
        self.ui.cb_write_meta.setEnabled(False)
        self.ui.cb_write_lab.setEnabled(False)
        self.ui.cb_write_arw.setEnabled(False)
        self.ui.cb_write_tif.setEnabled(False)
        self.ui.cb_write_animation.setEnabled(False)

        #
        self.ui.cb_write_meta_2.setEnabled(False)
        self.ui.cb_write_lab_2.setEnabled(False)
        self.ui.cb_write_arw_2.setEnabled(False)
        self.ui.cb_write_tif_2.setEnabled(False)
        self.ui.cb_write_animation_2.setEnabled(False)


        #分析の撮影設定1
        self.ui.rb_lane_number_1.setEnabled(False)
        self.ui.rb_lane_number_2.setEnabled(False)
        self.ui.rb_lane_number_3.setEnabled(False)
        self.ui.comb_camera_number.setEnabled(False)
        self.ui.cb_camera_operation_horizonal.setEnabled(False)
        self.ui.cb_camera_operation_vertical.setEnabled(False)
        self.ui.comb_lens.setEnabled(False)
        self.ui.comb_lens_adpter.setEnabled(False)
        self.ui.radioButton.setEnabled(False)
        self.ui.radioButton_2.setEnabled(False)
        self.ui.comb_pixel_shift_nulti_shooting.setEnabled(False)
        self.ui.e_shutter_speed.setEnabled(False)

        #分析の撮影設定2
        self.ui.e_color_temperatuer_1_1.setEnabled(False)
        self.ui.e_color_temperatuer_2_1.setEnabled(False)
        self.ui.e_color_temperatuer_3_1.setEnabled(False)
        self.ui.e_color_temperatuer_4_1.setEnabled(False)
        self.ui.e_color_temperatuer_5_1.setEnabled(False)
        self.ui.e_color_temperatuer_6_1.setEnabled(False)
        self.ui.e_color_temperatuer_7_1.setEnabled(False)
        self.ui.e_color_temperatuer_8_1.setEnabled(False)
        
        self.ui.e_color_temperatuer_1_2.setEnabled(False)
        self.ui.e_color_temperatuer_2_2.setEnabled(False)
        self.ui.e_color_temperatuer_3_2.setEnabled(False)
        self.ui.e_color_temperatuer_4_2.setEnabled(False)
        self.ui.e_color_temperatuer_5_2.setEnabled(False)
        self.ui.e_color_temperatuer_6_2.setEnabled(False)
        self.ui.e_color_temperatuer_7_2.setEnabled(False)
        self.ui.e_color_temperatuer_8_2.setEnabled(False)
        
        self.ui.e_color_temperatuer_1_3.setEnabled(False)
        self.ui.e_color_temperatuer_2_3.setEnabled(False)
        self.ui.e_color_temperatuer_3_3.setEnabled(False)
        self.ui.e_color_temperatuer_4_3.setEnabled(False)
        self.ui.e_color_temperatuer_5_3.setEnabled(False)
        self.ui.e_color_temperatuer_6_3.setEnabled(False)
        self.ui.e_color_temperatuer_7_3.setEnabled(False)
        self.ui.e_color_temperatuer_8_3.setEnabled(False)
        
        self.ui.e_color_temperatuer_1_4.setEnabled(False)
        self.ui.e_color_temperatuer_2_4.setEnabled(False)
        self.ui.e_color_temperatuer_3_4.setEnabled(False)
        self.ui.e_color_temperatuer_4_4.setEnabled(False)
        self.ui.e_color_temperatuer_5_4.setEnabled(False)
        self.ui.e_color_temperatuer_6_4.setEnabled(False)
        self.ui.e_color_temperatuer_7_4.setEnabled(False)
        self.ui.e_color_temperatuer_8_4.setEnabled(False)

        #分析後の加工設定
        self.ui.rb_grinding_1.setEnabled(False)
        self.ui.rb_grinding_2.setEnabled(False)
        self.ui.cmb_grinding_tools.setEnabled(False)
        self.ui.e_major_axis.setEnabled(False)
        self.ui.e_minor_axis.setEnabled(False)


        #保存設定に関する情報
        

    def change_temperature(self):
        l = []
        self.temperatures = []
        for i in range(4):
            l.append([self.color_temperatuers[i][0].text(),self.color_temperatuers[i][1].text(),self.color_temperatuers[i][2].text(),self.color_temperatuers[i][3].text(),self.color_temperatuers[i][4].text(),self.color_temperatuers[i][5].text(),self.color_temperatuers[i][6].text(),self.color_temperatuers[i][7].text()])
        for i in range(4):
            self.temperatures.append(list(dict.fromkeys([s for s in l[i] if s != ''])))

        self.temperatures = list(itertools.chain.from_iterable(self.temperatures))
    
    def light_source(self):
        self.light_pares = []
        l = []
        lights = []
        for i in range(4):
            l.append([self.comb_optical_types[i][0].currentText(),self.comb_optical_types[i][1].currentText(),self.comb_optical_types[i][2].currentText(),self.comb_optical_types[i][3].currentText(),self.comb_optical_types[i][4].currentText(),self.comb_optical_types[i][5].currentText(),self.comb_optical_types[i][6].currentText(),self.comb_optical_types[i][7].currentText()])
        for i in range(4):
            lights.append(list(dict.fromkeys([s for s in l[i] if s != 'None'])))

        lights = list(itertools.chain.from_iterable(lights))
        lights = [s for s in lights if s != '']

        if(len(lights)> 4):
            self.textBrowser_output("[ERROR]照明の種類が5種類以上選択されています。")
            self.textBrowser_output("   [INFO]選択された照明：" + '・'.join(lights))
            return False

        elif(len(lights)>= 1):

            for light in lights:
                target = light_changer(light)
                if(target != ''):
                    self.light_pares.append(target)
            return True 

        return False   

    def change_dsn(self):
        create_digital_name.CreateDN.display_name(self)

    def request_check(self):

        self.textBrowser_output('[MKDIR MODE START]')
        if(self.ui.l_tmp_volume.text() != "未選択"):
            try:
                for i_size in range(size):
                    dist_path = os.path.join(self.ui.l_tmp_volume.text() + '/tmp'+str(i_size))
                    os.mkdir(dist_path)
                    self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」を作成しました。')
            except:
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」は作成済みです。')

        elif(self.ui.l_output_volume.text() == "未選択") and (self.ui.l_tmp_volume.text() == "未選択"):
            try:
                for i_size in range(size):
                    dist_path = os.path.join(self.ui.l_input_volume.text() + '/tmp'+str(i_size))
                    os.mkdir(dist_path)
                    self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」を作成しました。')
        
            except:
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」は作成済みです。')

        else:
            try:
                for i_size in range(size):
                    dist_path = os.path.join(self.ui.l_output_volume.text() + '/tmp'+str(i_size))
                    os.mkdir(dist_path)
                    self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」を作成しました。')
        
            except:
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」は作成済みです。')
        
        if(self.ui.l_output_volume.text() == "未選択"):
            try:
                dist_path = os.path.join(self.ui.l_input_volume.text() , 'Lab_book')
                os.mkdir(dist_path)
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」を作りました。')
            except:
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」は作成済みです。')
            reply = QMessageBox.question(self, 'Viewerアプリチェック', '各mac mimiで「viewerアプリ」を起動して「' + self.ui.l_input_volume.text() + '/tmp0~' +str(size-1) +'」を選択してください。\nまた、保存先も同様に設定してください。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        else:
            try:
                dist_path = os.path.join(self.ui.l_output_volume.text() , 'Lab_book')
                os.mkdir(dist_path)
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」を作りました。')
            except:
                self.textBrowser_output('   [INFO]フォルダ「' + dist_path + '」は作成済みです。')
            reply = QMessageBox.question(self, 'Viewerアプリチェック', '各mac mimiで「viewerアプリ」を起動して「' + self.ui.l_output_volume.text() + '/tmp0~' +str(size-1) +'」を選択してください。\nまた、保存先も同様に設定してください。',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            return True
        else:
            return False
        

    def default_settings(self):
        self.change_cam_num()
        self.calc_voxel()
        self.ui.select_filters = []
        #アプリ起動時のラジオボタン初期値
        self.rb_sample_type = '岩石'
        self.name = "Taxon and/or lithology"
        self.rb_selected_dataset = '無'
        self.rb_selected_voxel = '無'
        self.rb_selected_related_samples = '無'
        self.rb_selected_presence_active = '有'
        self.rb_selected_stlle_plate_active = '有'
        self.rb_selected_network = 'LAN'
        self.rb_camera_direction = '横置き'

        self.grinding_tools = 'カップ型砥石'
        self.select_filters = []
        self.light_pares = []
        self.temperature_pare = []
        self.voxel_pare = []
        self.temperatures = []

        self.rb_animation_opt = "まとめて作成"
        self.rb_lto_opt = "正のみ"
        
        self.rb_full_opt = "FullSet"
        

        #アプリ起動時の試料情報表
        self.ui.l_taxon_lithology.setText('化石・岩石種')
        hides = [self.ui.l_time_date_collection_2,self.ui.e_time_and_date_of_collection,self.ui.l_age,self.ui.e_age,self.ui.l_sex,self.ui.e_sex,
               self.ui.l_strage_condition,self.ui.e_strage_condition,self.ui.e_other_adpter,self.ui.e_other_interval,self.ui.e_other_preparation,self.ui.e_other_filter]
        
        for i in range(len(hides)):
            hides[i].hide()

        #チェックボックス用のスクロールエリアを隠しておく
        self.ui.scrl_cb_area.hide()

        self.ui.l_output_volume_huku.setText("「正のみ」に設定されています。")
        self.ui.b_output_volume_huku.setDisabled(True)

        self.ui.rb_rb_nokosu_opt = "残す"

        
    def sub_win(self):
        subWindow = show_table.Ui_Form()
        # サブウィンドウの表示
        subWindow.show()

    def calc_voxel(self):
        self.ui.voxels = []
        for i in range(len(self.e_frequencys)):
            try:
                cal = float(self.ui.e_total_grinding_thickness_in_each_cycle.text()) * float(self.e_frequencys[i].text())
                cal = Decimal(str(cal))
                cal = cal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                self.ui.voxels.append(cal)
                
            except:
                self.ui.voxels.append('')
    def log_output(self):
        self.textBrowser_output('[LAB BOOK MODE START]')
        CreateLog.MakeLogFile(self,self.rb_sample_type,self.grinding_tools)
        self.textBrowser_output('    [INFO]出力されました。')
        self.textBrowser_output('[LAB BOOK MODE END]')
        self.textBrowser_output('------------------------------------------')
        if(self.ui.cw_log_output.isChecked == True):
            self.chat_message_send('LAB BOOK 出力：完了')

    def log_re_output(self):
        self.textBrowser_output('[RE LAB BOOK MODE START]')
        CreateLog.MakeLogFile(self,self.rb_sample_type,self.grinding_tools)
        self.textBrowser_output('    [INFO]出力されました。')
        self.textBrowser_output('[RE LAB BOOK MODE END]')
        self.textBrowser_output('------------------------------------------')
        if(self.ui.cw_log_output.isChecked == True):
            self.chat_message_send('LAB BOOK 再出力：完了')

    def digital_names(self):
        flag = self.light_source()
        create_digital_name.CreateDN.display_name(self)

        comb_individual_number_of_lights = [[self.ui.comb_individual_number_of_light_1_1,self.ui.comb_individual_number_of_light_2_1,self.ui.comb_individual_number_of_light_3_1,self.ui.comb_individual_number_of_light_4_1,self.ui.comb_individual_number_of_light_5_1,self.ui.comb_individual_number_of_light_6_1,self.ui.comb_individual_number_of_light_7_1,self.ui.comb_individual_number_of_light_8_1],
        [self.ui.comb_individual_number_of_light_1_2,self.ui.comb_individual_number_of_light_2_2,self.ui.comb_individual_number_of_light_3_2,self.ui.comb_individual_number_of_light_4_2,self.ui.comb_individual_number_of_light_5_2,self.ui.comb_individual_number_of_light_6_2,self.ui.comb_individual_number_of_light_7_2,self.ui.comb_individual_number_of_light_8_2],
        [self.ui.comb_individual_number_of_light_1_3,self.ui.comb_individual_number_of_light_2_3,self.ui.comb_individual_number_of_light_3_3,self.ui.comb_individual_number_of_light_4_3,self.ui.comb_individual_number_of_light_5_3,self.ui.comb_individual_number_of_light_6_3,self.ui.comb_individual_number_of_light_7_3,self.ui.comb_individual_number_of_light_8_3],
        [self.ui.comb_individual_number_of_light_1_4,self.ui.comb_individual_number_of_light_2_4,self.ui.comb_individual_number_of_light_3_4,self.ui.comb_individual_number_of_light_4_4,self.ui.comb_individual_number_of_light_5_4,self.ui.comb_individual_number_of_light_6_4,self.ui.comb_individual_number_of_light_7_4,self.ui.comb_individual_number_of_light_8_4]]

        for i in range(len(comb_individual_number_of_lights)): 
            for j in range(len(comb_individual_number_of_lights[0])): 
                if(self.comb_optical_types[i][j].currentText() == 'PA') or (self.comb_optical_types[i][j].currentText() == 'PB') or (self.comb_optical_types[i][j].currentText() == 'RLS') or (self.comb_optical_types[i][j].currentText() == 'RLL'):
                    self.color_temperatuers[i][j].setEnabled(True)
                    self.color_temperatuers[i][j].setText("5600K") 
                    self.change_temperature()
                elif(self.comb_optical_types[i][j].currentText() == 'GN6000') or (self.comb_optical_types[i][j].currentText() == 'RL6000'):
                    self.color_temperatuers[i][j].setEnabled(True)
                    self.color_temperatuers[i][j].setText("6200K") 
                    self.change_temperature()
                elif(self.comb_optical_types[i][j].currentText() == 'GN9000') or (self.comb_optical_types[i][j].currentText() == 'RL9000'):
                    self.color_temperatuers[i][j].setEnabled(True)
                    self.color_temperatuers[i][j].setText("6500K") 
                    self.change_temperature()
                elif(self.comb_optical_types[i][j].currentText() == ''):
                    self.color_temperatuers[i][j].clear()
                    self.color_temperatuers[i][j].setEnabled(False)
                    self.change_temperature()
                else:
                    self.color_temperatuers[i][j].setText("None")
                    self.color_temperatuers[i][j].setEnabled(False)
                    self.change_temperature()

        for i in range(len(comb_individual_number_of_lights)): 
            for j in range(len(comb_individual_number_of_lights[0])): 
                current_text = comb_individual_number_of_lights[i][j].currentText()
                comb_individual_number_of_lights[i][j].clear()
                comb_individual_number_of_lights[i][j].setEnabled(True)
                if(self.comb_optical_types[i][j].currentText() == 'PA'):
                    distL = ['01','02','03','04','05','06','07','08','09','10']
                elif(self.comb_optical_types[i][j].currentText() == 'PB'):
                    distL = ['01','02','03','04','05','06','07','08','09','10','11','12']
                elif(self.comb_optical_types[i][j].currentText() == 'HP-365'):
                    distL = ['01','02','03','04']
                elif(self.comb_optical_types[i][j].currentText() == 'SP365'):
                    distL = ['01','02','03','04','05','06']
                elif(self.comb_optical_types[i][j].currentText() == 'SP530') or (self.comb_optical_types[i][j].currentText() == 'SP590'):
                    distL = ['01','02']
                else:
                    distL = ['']
                    comb_individual_number_of_lights[i][j].clear()
                    comb_individual_number_of_lights[i][j].setEnabled(False)

                comb_individual_number_of_lights[i][j].addItems(distL)
                if(current_text in distL):
                    comb_individual_number_of_lights[i][j].setCurrentText(current_text)
                

        

        
 
    def disable_kugiri(self):
        if(self.ui.cmb_grinding_tools.currentText() == '-------------------------------------'):
            self.ui.cmb_grinding_tools.setCurrentText('SD-800-I-75-M40, Noritake Co., Limited')

    def change_cam_num(self):

        dist_list = []
        
        if('α7R' in self.ui.comb_camera_number.currentText()):
            
            self.ui.comb_pixel_shift_nulti_shooting.setDisabled(False)
            if('PSMS16' in self.ui.comb_pixel_shift_nulti_shooting.currentText()):
                self.ui.e_major_axis.setText('19008')
                self.ui.e_minor_axis.setText('12672')
                
            else:
                self.ui.e_major_axis.setText('9504')
                self.ui.e_minor_axis.setText('6336')
            dist_list = ['not','PSMS4','PSMS16']
        
        elif('GFX 100s' in self.ui.comb_camera_number.currentText()):
            self.ui.comb_pixel_shift_nulti_shooting.setDisabled(False)
            if('PSMS16' in self.ui.comb_pixel_shift_nulti_shooting.currentText()):
                self.ui.e_major_axis.setText('23296')
                self.ui.e_minor_axis.setText('17472')
            else:
                self.ui.e_major_axis.setText('11648')
                self.ui.e_minor_axis.setText('8736')
            dist_list = ['not','PSMS4','PSMS16']
        
        else:   #5Ds, 5DsR            
            self.ui.comb_pixel_shift_nulti_shooting.setDisabled(True)
            self.ui.comb_pixel_shift_nulti_shooting.setCurrentText("not")
            self.ui.e_major_axis.setText('8688')
            self.ui.e_minor_axis.setText('5792')

            dist_list = ['not','PSMS16']


        if(self.ui.comb_pixel_shift_nulti_shooting.currentText() == "not"):
            self.ui.comb_interval_of_psms.setEnabled(False)
            self.ui.comb_interval_of_psms.clear()
            self.ui.comb_interval_of_psms.addItems([""])
        else:
            self.ui.comb_interval_of_psms.setEnabled(True)
            self.ui.comb_interval_of_psms.clear()
            self.ui.comb_interval_of_psms.addItems(["shortest",'1"','2"','3"','other'])

        
        self.scale()

    def rb_diamond_bite_cliked(self):
        radioBtn = self.sender()
        self.grinding_tools = radioBtn.text()
        
        if(self.grinding_tools == '単結晶ダイヤモンドバイト'):
            self.ui.cmb_grinding_tools.hide()
        else:
            self.ui.cmb_grinding_tools.show()

    def main_action(self):
        if(self.ui.cb_same_time_mode.isChecked() == True):
            reply = QMessageBox.question(self, 'モード確認', '「同時実行モード」が有効です。 \n「yes」を選択すると、'+self.ui.l_input_volume.text() + 'にあるデータは削除され、プログラムが実行されます',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            self.textBrowser_output('[ERROR]実装中の機能です！アプリ動作終了。')
        else:
            reply = QMessageBox.question(self, 'モード確認', '「同時実行モードが」無効です。\n対象フォルダ内のファイル削除をせずに、プログラムが実行されます。\nこのアプリで設定されているレーン番号は「'+ str(['1','2','3'][int(self.ui.bg_lane.checkedId()) * (-1) - 2])+'」です。',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if(self.ui.cw_start.isChecked() == True):
                self.chat_message_send('【開始】')
            self.contents_disable()
            self.ui.b_stop.setDisabled(False)
            self.ui.b_start.setDisabled(True)

            now = datetime.datetime.now()
            self.ui.t_start_time.setText(now.strftime('%Y-%m-%d %H:%M:%S'))

            #ボタン編集不可
            #self.contents_able()
            #self.log_output()

            if(self.ui.cw_log_output.isChecked() == True):
                self.chat_message_send('ログ出力：完了')
            
            global ARW_COMBINATION_NUMBER
            if(self.ui.comb_pixel_shift_nulti_shooting.currentText() == "PSMS16"):
                ARW_COMBINATION_NUMBER = 16
            elif(self.ui.comb_pixel_shift_nulti_shooting.currentText() == "PSMS4"):
                ARW_COMBINATION_NUMBER = 4
            else: #self.ui.comb_pixel_shift_nulti_shooting.currentText() == "not"
                ARW_COMBINATION_NUMBER = 1



            self.execAction = ActionThread()
            self.execAction.ui = self.ui
            self.execAction.pixel_shift = self.ui.comb_pixel_shift_nulti_shooting.currentText()
            """
            self.execAction.printThread.connect(self.printLog)
            self.execAction.rb_sample_type = self.rb_sample_type
            self.execAction.taxon_lithology = self.name
            self.execAction.counter = 0
            self.execAction.light_type_names = self.light_type_names
            self.execAction.positions = self.positions
            self.execAction.temperatures = self.temperatures
            self.execAction.camera_name = self.ui.comb_camera_number.currentText()
            self.execAction.selected_mode = self.rb_sample_type
            self.execAction.select_filters = self.select_filters
            self.execAction.temperature_pare = self.temperature_pare
            self.execAction.voxel_pare = self.voxel_pare
            self.execAction.grinding_tools = self.grinding_tools
            self.execAction.picture_nums = self.picture_nums
            self.execAction.comm = comm
            self.execAction.size = size
            self.execAction.rb_animation_opt = self.rb_animation_opt
            self.execAction.innerWidget1 = self.innerWidget1
            self.execAction.innerWidget2 = self.innerWidget2
            self.execAction.rb_lto_opt = self.rb_lto_opt    
            """        
            self.execAction.start()
            
            self.SyncThread = SyncThread()
            self.SyncThread.ui = self.ui
            self.SyncThread.ARW_NUMBER = ARW_COMBINATION_NUMBER
            self.SyncThread.printThread.connect(self.printLog_sync)
            self.SyncThread.start()
            

        else:
            self.chat_message_send('[WARNING!]実行がキャンセルされました')
    def printLog(self, line):
        self.textBrowser_output(line)

    def printLog_sync(self, line):
        self.ui.tb_sync.append(line)

    def rb_clicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_sample_type = radioBtn.text()
            self.textBrowser_output('[EVENT]「' + self.rb_sample_type + '」に変更されました。')

            shows = [self.ui.l_geological_age,self.ui.e_geological_age,self.ui.e_geological_age_2,self.ui.l_horizon,self.ui.e_horizon,self.ui.l_locality,self.ui.e_locality_2,self.ui.e_locality,self.ui.l_latitude,self.ui.e_latitude,self.ui.l_longitude,self.ui.e_longitude,self.ui.l_time_date_collection_2,self.ui.e_time_and_date_of_collection,self.ui.l_age,self.ui.e_age,self.ui.l_sex,self.ui.e_sex,self.ui.l_strage_condition,self.ui.e_strage_condition,self.ui.e_horizon_2]
            for i in range(len(shows)):
                shows[i].show()

            if(self.rb_sample_type == '岩石'):
                self.ui.l_taxon_lithology.setText('化石・岩石種')        
                self.name = "Taxon and/or lithology"
                hides = [self.ui.l_time_date_collection_2,self.ui.e_time_and_date_of_collection,self.ui.l_age,self.ui.e_age,self.ui.l_sex,self.ui.e_sex,self.ui.l_strage_condition,self.ui.e_strage_condition]

            elif(self.rb_sample_type == '生物'):
                self.ui.l_taxon_lithology.setText('学名')     
                self.name = "Binominal name"
                hides = [self.ui.l_geological_age,self.ui.e_geological_age,self.ui.e_geological_age_2,self.ui.l_horizon,self.ui.e_horizon,self.ui.e_horizon_2]

            else:
                self.ui.l_taxon_lithology.setText('試料名')     
                self.name = "Sample type name"
                hides = [self.ui.l_geological_age,self.ui.e_geological_age,self.ui.e_geological_age_2,self.ui.l_horizon,self.ui.e_horizon,self.ui.e_horizon_2,self.ui.l_locality,self.ui.e_locality,self.ui.e_locality_2,self.ui.l_latitude,self.ui.e_latitude,self.ui.l_longitude,self.ui.e_longitude,self.ui.l_time_date_collection_2,self.ui.e_time_and_date_of_collection,self.ui.l_age,self.ui.e_age,self.ui.l_sex,self.ui.e_sex,self.ui.l_strage_condition,self.ui.e_strage_condition,self.ui.e_time_and_date_of_collection]

            for i in range(len(hides)):
                hides[i].hide()

    def rb_dataset_active_clicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_selected_dataset = radioBtn.text()
            if(self.rb_selected_dataset == '有'):
                self.ui.e_correspondence_of_datasets.setDisabled(False)
                
            else:
                self.ui.e_correspondence_of_datasets.setDisabled(True)
                self.ui.e_depository.setDisabled(True)
                self.ui.e_depository.setText("")
                self.ui.e_correspondence_of_datasets.setPlainText("")
                

    def rb_voxel_active_clicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_selected_voxel = radioBtn.text()
            if(self.rb_selected_voxel == '有'):
                self.ui.e_changes_in_voxel_z_width_within_a_same_dataset.setDisabled(False)
            else:
                self.ui.e_changes_in_voxel_z_width_within_a_same_dataset.setDisabled(True)
                self.ui.e_changes_in_voxel_z_width_within_a_same_dataset.setPlainText("")


    def rb_related_samples_clicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_selected_related_samples = radioBtn.text()
            if(self.rb_selected_related_samples == '有'):
                self.ui.e_detailed_information.setDisabled(False)
                self.ui.e_depository.setDisabled(False)
                self.ui.e_depository.setText('国立科学博物館')
            else:
                self.ui.e_detailed_information.setDisabled(True)
                self.ui.e_detailed_information.setPlainText("")
                self.ui.e_depository.setDisabled(True)
                self.ui.e_depository.setText('')

    def rb_presence_active_clicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_selected_presence_active = radioBtn.text()

    def rb_stlle_plate_active_clicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_selected_stlle_plate_active = radioBtn.text()

    def rb_network_cliked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():
            self.rb_selected_network = radioBtn.text()

    def cb_presence3(self,state):
        if state == 0:
            self.ui.e_file_name.setEnabled(False)
        else:
            self.ui.e_file_name.setEnabled(True)

    
    def cb_prepared(self,state):

        if state == 0:
            self.ui.comb_details_of_preparation.clear()
            self.ui.comb_details_of_preparation.setEnabled(False)
            self.ui.e_other_preparation.setEnabled(False)

        else:
            self.ui.comb_details_of_preparation.addItems(["接着","表面の被覆","空隙の充填","その他"])
            self.ui.comb_details_of_preparation.setEnabled(True)
            self.ui.e_other_preparation.setEnabled(True)
    

    def stop_button(self):
        self.stop_flag = True
        self.is_true(self.ui.e_total_grinding_thickness.text(),'・総加工量(mm)')
        self.is_true(self.ui.e_specimen_storage_area.text(),'・標本保管場所')

        if(self.stop_flag == False):
            self.textBrowser_output('[ERROR!]上記の内容が未記入のため、終了できません。')
        else:
            self.textBrowser_output('[EVENT]終了ボタンが押されました。')
            self.ui.b_stop.setDisabled(True)
            self.ui.b_start.setDisabled(False)


    def is_true(self,target,str):
        if target:
            pass
        else:
            self.ui.textBrowser.append(str)
            self.ui.textBrowser_2.append(str)
            self.stop_flag =False

    def select_other(self):
        if(str(self.ui.comb_lens_adpter.currentText()) == 'others'):
            self.ui.e_other_adpter.show()
        else:
            self.ui.e_other_adpter.hide()

        if(str(self.ui.comb_interval_of_psms.currentText()) == 'other'):
            self.ui.e_other_interval.show()
        else:
            self.ui.e_other_interval.hide()

        if(str(self.ui.comb_details_of_preparation.currentText()) == 'その他'):
            self.ui.e_other_preparation.show()
        else:
            self.ui.e_other_preparation.hide()   

        if(self.ui.cb_other_filter.checkState() != 0):
            self.ui.e_other_filter.show()
        else:
            self.ui.e_other_filter.hide()      

    def text_trash(self):
        self.ui.textBrowser.clear()
        self.ui.textBrowser_2.clear()

    def exec_button(self):

        exec_flag = True
        """
        if(self.lane_checker() == False):
            exec_flag = False
            self.textBrowser_output('[ERROR!]撮影条件一覧の情報に誤りがあります。')
            self.textBrowser_output('   [MESSAGE]「Bタブ」の「分析の撮影設定1」のレーン番号が、「Bタブ」の「分析の撮影設定3」のレーン番号内に含まれているか確認してください。')

        if(check_input.default_necessary(self) == False):
            exec_flag = False

        if(check_input.special_necessary(self,self.rb_sample_type) == False):
            exec_flag = False

        #フィルターチェック
        if(self.ui.cb_other_filter.checkState() != 0) and (self.select_filters == []):
            self.select_filters.append(self.ui.e_other_filter.text())
        if(self.select_filters == []):
            exec_flag = False
            self.textBrowser_output('・フィルター')
            self.ui.l_filter.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_polishing.setStyleSheet("QLabel { color : black; }")

        if(self.position_checker() == False):
            exec_flag = False
            self.textBrowser_output('・撮影位置')
            self.ui.l_filter.setStyleSheet("QLabel { color : red; }")
        
        if(exec_flag == False):
            self.textBrowser_output('[ERROR!]入力必須項目が一部不足しています')

        if(self.light_source() == False):
            self.textBrowser_output('[ERROR!]「照明の種類」が統一されていません。')
            exec_flag = False


        if(check_input.shooting_list_checker(self) == False):
            self.textBrowser_output('[ERROR!]「撮影条件一覧」に未入力項目があります。')
            exec_flag = False

        if(len(self.innerWidget1.LneEdts) != size) or (self.innerWidget1.LneEdts[0].text() == ""):
            self.textBrowser_output('[ERROR!]「KM1」がSize数より少ないです。')
            self.textBrowser_output('   [MESSAGE]「KM1」の設定が正しいか確認してください。')
            exec_flag = False

        if(len(self.innerWidget2.LneEdts) != size) or (self.innerWidget2.LneEdts[0].text() == ""):
            self.textBrowser_output('[ERROR!]「KM2」がSize数より少ないです。')
            self.textBrowser_output('   [MESSAGE]「KM2」の設定が正しいか確認してください。')
            exec_flag = False

        if(self.connect_check() == False):
            self.textBrowser_output('[ERROR!]「ARW保存先フォルダ」に接続できません。')
            self.textBrowser_output('   [MESSAGE]「ARW保存先フォルダ」のパスが正しいか確認してください。')
            exec_flag = False

        if(self.temperatures == []):
            self.textBrowser_output('[ERROR!]「色温度」が設定されていません。')
            self.textBrowser_output('   [MESSAGE]「照明1~4」の「色温度」がそれぞれ入力されているか確認してください。')
            exec_flag = False
        
        elif(len(self.temperatures) > 4):
            self.textBrowser_output('[ERROR!]「色温度」が5種類以上設定されています。')
            self.textBrowser_output('   [MESSAGE]「照明1~4」の「色温度」がそれぞれ入力されているか確認してください。')
            exec_flag = False
        """
        
        if(exec_flag == True):
            if(self.request_check() == False):
                self.textBrowser_output('[ERROR!]「Viewer」アプリを起動してください。')
                
                if(self.ui.l_output_volume.text() == "未選択") and (self.ui.l_tmp_volume.text() == "未選択"):
                    self.textBrowser_output('[ERROR!]「' + self.ui.l_input_volume.text() + '/tmp' +'」を選択してください。')
                elif(self.ui.l_tmp_volume.text() != "未選択"):
                    self.textBrowser_output('[ERROR!]「' + self.ui.l_tmp_volume.text() + '/tmp' +'」を選択してください。')
                else:
                    self.textBrowser_output('[ERROR!]「' + self.ui.l_output_volume.text() + '/tmp' +'」を選択してください。')

            else:
                self.main_action()
        else:
            self.textBrowser_output('[ERROR!]上記メッセージを確認してください。')

    def connect_check(self):
        if(self.ui.l_output_volume.text() == "未選択") and (self.ui.l_tmp_volume.text() == "未選択"):
            return os.path.isdir(self.ui.l_input_volume.text())
        elif(self.ui.l_tmp_volume.text() != "未選択"):
            return os.path.isdir(self.ui.l_tmp_volume.text())
        else:
            return os.path.isdir(self.ui.l_output_volume.text())

    def position_checker(self):
        result = True
        for i in range(len(self.photoraphing_positions_label)):
            self.photoraphing_positions_label[i].setStyleSheet("QLabel { color : black; }")

        for i in range(len(self.positions)):
            if(self.photoraphing_positions[int(self.positions[i])-1].text() == ""):
                self.photoraphing_positions_label[int(self.positions[i])-1].setStyleSheet("QLabel { color : red; }")
                result = False
            else:
                self.photoraphing_positions_label[int(self.positions[i])-1].setStyleSheet("QLabel { color : black; }")
    
        return result

    def scale_set_position(self):
        radioBtn = self.sender()
        self.rb_camera_direction = '横置き'
        if radioBtn.isChecked():
            self.rb_camera_direction = radioBtn.text()
            self.textBrowser_output('[EVENT]「' + self.rb_camera_direction + '」に変更されました。')

        self.scale()

    def scale(self):
        try:
            cal = float(self.ui.e_grid_A_1.text()) - float(self.ui.e_grid_B_1.text())
            cal = Decimal(str(cal))
            cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            self.ui.e_grid_C_1.setText(str(abs(cal)))
        except:
            self.ui.e_grid_C_1.setText('error')
        try:
            cal = float(self.ui.e_grid_A_2.text()) - float(self.ui.e_grid_B_2.text())
            cal = Decimal(str(cal))
            cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            self.ui.e_grid_C_2.setText(str(abs(cal)))
        except:
            self.ui.e_grid_C_2.setText('error')
        try:
            cal = float(self.ui.e_grid_A_3.text()) - float(self.ui.e_grid_B_3.text())
            cal = Decimal(str(cal))
            cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            self.ui.e_grid_C_3.setText(str(abs(cal)))
        except:
            self.ui.e_grid_C_3.setText('error')
        try:
            cal = float(self.ui.e_grid_A_4.text()) - float(self.ui.e_grid_B_4.text())
            cal = Decimal(str(cal))
            cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            self.ui.e_grid_C_4.setText(str(abs(cal)))
        except:
            self.ui.e_grid_C_4.setText('error')
        try:
            cal = float(self.ui.e_grid_A_5.text()) - float(self.ui.e_grid_B_5.text())
            cal = Decimal(str(cal))
            cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            self.ui.e_grid_C_5.setText(str(abs(cal)))
        except:
            self.ui.e_grid_C_5.setText('error')

        try:
            #グリッドXの平均値
            average = (float(self.ui.e_grid_C_1.text()) + float(self.ui.e_grid_C_2.text()) + float(self.ui.e_grid_C_3.text()) + float(self.ui.e_grid_C_4.text()) + float(self.ui.e_grid_C_5.text())) / 5
            
            bairitsu = 1.5
            if('α7R IV' in self.ui.comb_camera_number.currentText()):
                kakudai = 11.9
            elif('GFX 100s' in self.ui.comb_camera_number.currentText()):
                kakudai = 24
                bairitsu = 4/3
            else:
                kakudai = 18

            #横置きの場合
            if(self.rb_camera_direction == '横置き'):
                try:
                    cal = average * kakudai
                    cal = Decimal(str(cal))
                    cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                    self.ui.e_fov.setText(str(cal))
                except:
                    self.ui.e_fov.setText('error')
                try:
                    cal = average * kakudai * 1000 / float(self.ui.e_major_axis.text())
                    cal = Decimal(str(cal))
                    cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                    self.ui.e_pixel_width.setText(str(cal))
                except:
                    self.ui.e_pixel_width.setText('error')
            else:
                try:
                    cal = average * kakudai * bairitsu
                    cal = Decimal(str(cal))
                    cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                    self.ui.e_fov.setText(str(cal))
                except:
                    self.ui.e_fov.setText('error')
                try:
                    cal = average * kakudai * 1000 / float(self.ui.e_minor_axis.text())
                    cal = Decimal(str(cal))
                    cal = cal.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                    self.ui.e_pixel_width.setText(str(cal))
                except:
                    self.ui.e_pixel_width.setText('error')
        except:
            pass


    def textBrowser_output(self,message):
        message = str(message)
        self.ui.textBrowser.append(message)
        self.ui.textBrowser_2.append(message)

    def setting_output(self):
        try:
            dist_path = os.path.join(os.getcwd() , 'settings')
            os.mkdir(dist_path)
        except:
            pass
    
        if(check_input.default_necessary(self) == False) or (check_input.special_necessary(self,self.rb_sample_type) == False):
            self.textBrowser_output('[ERROR!]上記の内容が未記入のため、出力できません。')
        
        else:
            now = datetime.datetime.now()
            fileName = os.path.join(os.getcwd() , 'settings','settings_' + now.strftime('%Y%m%d_%H%M') + '.ini')
            config = configparser.ConfigParser()

            config['lane'] = {}
            config['lane']['e_digital_specimen_number'] =  self.ui.e_digital_specimen_number.text()
            
            config['lane']['e_date_of_analys'] =  self.ui.e_date_of_analys.text()
            config['lane']['e_name_of_analyst'] =  self.ui.e_analyst.text()
            config['lane']['e_affiliations'] =  self.ui.e_affiliations.text()
            
            config['lane']['e_input_path'] =  self.ui.l_input_volume.text()
            config['lane']['e_output_path'] =  self.ui.l_output_volume.text()
            config['lane']['e_tmp_path'] =  self.ui.l_tmp_volume.text()
            config['lane']['e_output_path_sei'] =  self.ui.l_output_volume_sei.text()
            config['lane']['e_output_path_huku'] =  self.ui.l_output_volume_huku.text()

            #試料情報
            config['lane']['e_laboratory_identification_number'] =  self.ui.e_laboratory_identificiation_number.text()
            config['lane']['e_public_collection_number_destructive_analysis'] =  self.ui.e_puglic_collection_number_before_destructive_analysis.text()
            config['lane']['e_taxon_lithology'] =  self.ui.e_taxon_lithology.text()
            config['lane']['e_locality'] =  self.ui.e_locality.text()
            config['lane']['e_locality_2'] =  self.ui.e_locality_2.text()
            config['lane']['sample_type'] =  self.rb_sample_type
            config['lane']['e_geological_age'] =  self.ui.e_geological_age.text()
            config['lane']['e_geological_age_2'] =  self.ui.e_geological_age_2.text()
            config['lane']['e_horizon'] =  self.ui.e_horizon.text()
            config['lane']['e_horizon_2'] =  self.ui.e_horizon_2.text()
            config['lane']['e_latitude'] =  self.ui.e_latitude.text()
            config['lane']['e_longitude'] =  self.ui.e_longitude.text()
            config['lane']['e_time_date_collection'] =  self.ui.e_time_and_date_of_collection.text()
            config['lane']['e_age'] =  self.ui.e_age.text()
            config['lane']['e_sex'] =  self.ui.e_sex.text()
            config['lane']['e_storage_condition'] =  self.ui.e_strage_condition.text()
            config['lane']['e_sample_provider'] =  self.ui.e_sample_provider.text()
            config['lane']['e_references'] =  self.ui.e_references.text()
            config['lane']['e_sample_photo_before_destuctive_analysis'] =  self.ui.e_file_name.text()
            config['lane']['e_sample_size'] =  self.ui.e_size_of_sample.text()
            config['lane']['e_sample_weight'] =  self.ui.e_weight_of_sample.text()

            #試料処理
            config['lane']['cb_prepared_or_not'] = str(self.ui.cb_prepared_or_not.checkState())
            config['lane']['comb_details_of_preparation'] =  self.ui.comb_details_of_preparation.currentText()
            config['lane']['cb_alminum_powder'] =  self.ui.comb_aluminium_powder.currentText()
            config['lane']['e_size_of_prepared_sample'] =  self.ui.e_size_of_prepared_sample.text()
            config['lane']['e_weight_of_prepared_sample'] =  self.ui.e_weight_of_prepared_sample.text()

            #証明機材と証明設定
            for i in range(len(self.photoraphing_positions)):
                config['lane']['e_photoraphing_position_' + str(i + 1)] =  self.photoraphing_positions[i].text()
            #レーン番号
            for i in range(len(self.all_lane_numbers)):
                config['lane']['cb_lane_' + str(i + 1)] =  self.all_lane_numbers[i].currentText()
            #照明番号
            for i in range(len(self.e_lights)):
                config['lane']['e_light_' + str(i + 1)] =  self.e_lights[i].text()
            #撮影位置
            for i in range(len(self.e_position_nos)):
                config['lane']['e_position_no_' + str(i + 1)] =  self.e_position_nos[i].text()
            #コート
            for i in range(len(self.e_corts)):
                config['lane']['e_cort_' + str(i + 1)] =  self.e_corts[i].text()
            #ブロー
            for i in range(len(self.e_blows)):
                config['lane']['e_blow_' + str(i + 1)] =  self.e_blows[i].text()
            #撮影間隔
            for i in range(len(self.e_frequencys)):
                config['lane']['e_frequency_' + str(i + 1)] =  self.e_frequencys[i].text()
            #撮影信号
            for i in range(len(self.e_photographing_signals)):
                config['lane']['e_photographing_signals_' + str(i + 1)] =  self.e_photographing_signals[i].text()
            #撮影前
            for i in range(len(self.e_wating_time_bs)):
                config['lane']['e_wating_time_b_' + str(i + 1)] =  self.e_wating_time_bs[i].text()
            #撮影後
            for i in range(len(self.e_wating_time_as)):
                config['lane']['e_wating_time_a_' + str(i + 1)] =  self.e_wating_time_as[i].text()
            #分析の加工設定
            config['lane']['e_total_grinding_thickness'] = self.ui.e_total_grinding_thickness.text()
            config['lane']['e_total_replacement'] =  self.ui.e_total_grinding_thickness_in_each_cycle.text()
            config['lane']['e_servo'] =  self.ui.e_total_grinding_thickness_in_each_finishing_process.text()
            config['lane']['e_rough_cutting_volume'] =  self.ui.e_depth_of_cut_in_rough_grinding.text()
            config['lane']['e_total_cutting_volume'] =  self.ui.e_depth_of_cut_in_finish_grinding.text()
            config['lane']['e_processing_speed'] =  self.ui.e_rough_grinding_speed.text()
            config['lane']['e_finishing_speed'] =  self.ui.e_finish_grinding_speed.text()
            config['lane']['e_contrast_speed'] =  self.ui.e_coating_speed.text()
            config['lane']['e_broaching_speed'] =  self.ui.e_blowing_speed.text()
            config['lane']['e_number_of_spacers'] =  self.ui.e_polishing.text()

            config['lane']['cb_crystal_diamond_bite'] =  self.grinding_tools
            config['lane']['rb_grinding_1'] = str(self.ui.rb_grinding_1.isChecked())
            config['lane']['rb_grinding_2'] = str(self.ui.rb_grinding_2.isChecked())
            config['lane']['cmb_griding_tools'] =  self.ui.cmb_grinding_tools.currentText()

            config['lane']['rb_selected_dataset'] =  self.rb_selected_dataset
            config['lane']['rb_selected_voxel'] =  self.rb_selected_voxel
            config['lane']['rb_selected_related_samples'] =  self.rb_selected_related_samples
            config['lane']['rb_selected_presence'] =  self.rb_selected_presence_active
            config['lane']['rb_selected_stlle_plate'] =  self.rb_selected_stlle_plate_active

            config['lane']['e_specimen_storage_area'] =  self.ui.e_specimen_storage_area.text()
            config['lane']['e_datasets'] =  self.ui.e_correspondence_of_datasets.toPlainText()
            config['lane']['e_voxel'] =  self.ui.e_changes_in_voxel_z_width_within_a_same_dataset.toPlainText()
            config['lane']['e_note'] =  self.ui.e_notes.toPlainText()
            config['lane']['e_specimen_storage_area_3'] =  self.ui.e_detailed_information.toPlainText()
            #斜体
            config['lane']['cb_shatai'] = str(self.ui.cb_shatai.checkState())

            with open(fileName, 'w') as file:
                config.write(file)
            
            self.textBrowser_output('[EVENT]「' + fileName + '」を出力しました。')
        

    def setting_input(self):
        # 第二引数はダイアログのタイトル、第三引数は表示するパス
        dist_path = os.path.join(os.getcwd() , 'settings')
        fname = QFileDialog.getOpenFileName(self, 'Open file', dist_path , '*.ini')
        
        try:
            dist_path = os.path.join(os.getcwd() , 'settings')
            os.mkdir(dist_path)
        except:
            pass

        try:
            config = configparser.ConfigParser()
            config.read(fname[0])
            
            #General取得
            self.ui.e_digital_specimen_number.setText(config['lane']['e_digital_specimen_number'])
            tdatetime = datetime.datetime.strptime(config['lane']['e_date_of_analys'], '%Y/%m/%d')
            self.ui.e_date_of_analys.setDate(QDate(tdatetime.year, tdatetime.month, tdatetime.day))
            self.ui.e_analyst.setText(config['lane']['e_name_of_analyst'])
            self.ui.e_affiliations.setText(config['lane']['e_affiliations'])

            #NAS連携取得
            self.ui.l_input_volume.setText(config['lane']['e_input_path'])
            self.ui.l_output_volume.setText(config['lane']['e_output_path'])
            self.ui.l_tmp_volume.setText(config['lane']['e_tmp_path'])
            self.ui.l_output_volume_sei.setText(config['lane']['e_output_path_sei'])
            self.ui.l_output_volume_huku.setText(config['lane']['e_output_path_huku'])

            #試料情報
            self.ui.e_laboratory_identificiation_number.setText(config['lane']['e_laboratory_identification_number'])
            self.ui.e_puglic_collection_number_before_destructive_analysis.setText(config['lane']['e_public_collection_number_destructive_analysis'])
            self.ui.e_taxon_lithology.setText(config['lane']['e_taxon_lithology'])
            self.ui.e_locality.setText(config['lane']['e_locality'])
            self.ui.e_locality_2.setText(config['lane']['e_locality_2'])
            
            self.ui.e_geological_age.setText(config['lane']['e_geological_age'])
            self.ui.e_geological_age_2.setText(config['lane']['e_geological_age_2'])
            self.ui.e_horizon.setText(config['lane']['e_horizon'])
            self.ui.e_horizon_2.setText(config['lane']['e_horizon_2'])
            self.ui.e_latitude.setText(config['lane']['e_latitude'])
            self.ui.e_longitude.setText(config['lane']['e_longitude'])
            tdatetime = datetime.datetime.strptime(config['lane']['e_time_date_collection'], '%Y/%m/%d')
            self.ui.e_time_and_date_of_collection.setDate(QDate(tdatetime.year, tdatetime.month, tdatetime.day))

            self.ui.e_age.setText(config['lane']['e_age'])
            self.ui.e_sex.setText(config['lane']['e_sex'])
            self.ui.e_strage_condition.setText(config['lane']['e_storage_condition'])
            self.ui.e_sample_provider.setText(config['lane']['e_sample_provider'])
            self.ui.e_references.setText(config['lane']['e_references'])
            self.ui.e_file_name.setText(config['lane']['e_sample_photo_before_destuctive_analysis'])

            if(config['lane']['e_sample_photo_before_destuctive_analysis'] != ''):
                self.ui.cb_presence_3.setChecked(True)
            self.ui.e_size_of_sample.setText(config['lane']['e_sample_size'])
            
            self.ui.e_weight_of_sample.setText(config['lane']['e_sample_weight'])
            self.ui.comb_details_of_preparation.setCurrentText(config['lane']['comb_details_of_preparation'])
            if(config['lane']['cb_prepared_or_not'] == '2'):
                self.ui.cb_prepared_or_not.setChecked(True)

            self.ui.comb_aluminium_powder.setCurrentText(config['lane']['cb_alminum_powder'])
            self.ui.e_size_of_prepared_sample.setText(config['lane']['e_size_of_prepared_sample'])
            self.ui.e_weight_of_prepared_sample.setText(config['lane']['e_weight_of_prepared_sample'])

            for i in range(len(self.photoraphing_positions)):
                self.photoraphing_positions[i].setText(config['lane']['e_photoraphing_position_' + str(i + 1)])
            
            for i in range(len(self.all_lane_numbers)):
                self.all_lane_numbers[i].setCurrentText(config['lane']['cb_lane_' + str(i + 1)])
            
            for i in range(len(self.e_lights)):
                self.e_lights[i].setText(config['lane']['e_light_' + str(i + 1)])
            
            for i in range(len(self.e_position_nos)):
                self.e_position_nos[i].setText(config['lane']['e_position_no_' + str(i + 1)])
            
            for i in range(len(self.e_corts)):
                self.e_corts[i].setText(config['lane']['e_cort_' + str(i + 1)])
                
            for i in range(len(self.e_blows)):
                self.e_blows[i].setText(config['lane']['e_blow_' + str(i + 1)])
                
            for i in range(len(self.e_frequencys)):
                self.e_frequencys[i].setText(config['lane']['e_frequency_' + str(i + 1)])
            
            for i in range(len(self.e_photographing_signals)):
                self.e_photographing_signals[i].setText(config['lane']['e_photographing_signals_' + str(i + 1)])
            
            for i in range(len(self.e_wating_time_bs)):
                self.e_wating_time_bs[i].setText(config['lane']['e_wating_time_b_' + str(i + 1)])
            
            for i in range(len(self.e_wating_time_as)):
                self.e_wating_time_as[i].setText(config['lane']['e_wating_time_a_' + str(i + 1)])
            
            self.ui.e_total_grinding_thickness.setText(config['lane']['e_total_grinding_thickness'])
            self.ui.e_total_grinding_thickness_in_each_cycle.setText(config['lane']['e_total_replacement'])
            self.ui.e_total_grinding_thickness_in_each_finishing_process.setText(config['lane']['e_servo'])
            self.ui.e_depth_of_cut_in_rough_grinding.setText(config['lane']['e_rough_cutting_volume'])
            self.ui.e_depth_of_cut_in_finish_grinding.setText(config['lane']['e_total_cutting_volume'])
            self.ui.e_rough_grinding_speed.setText(config['lane']['e_processing_speed'])
            self.ui.e_finish_grinding_speed.setText(config['lane']['e_finishing_speed'])
            self.ui.e_coating_speed.setText(config['lane']['e_contrast_speed'])
            self.ui.e_blowing_speed.setText(config['lane']['e_broaching_speed'])
            self.ui.e_polishing.setText(config['lane']['e_number_of_spacers'])
            
            if(config['lane']['rb_grinding_1'] == True):
                self.ui.rb_grinding_1.setChecked(True)
            else:
                self.ui.rb_grinding_2.setChecked(True)
            
            self.ui.cmb_grinding_tools.setCurrentText(config['lane']['cmb_griding_tools'])
            
            if(config['lane']['cb_crystal_diamond_bite'] == 'カップ型砥石'):
                self.ui.rb_grinding_1.setChecked(True)

            if(config['lane']['rb_selected_dataset'] == '有'):
                self.ui.rb_dataset_active.setChecked(True)
            if(config['lane']['rb_selected_voxel'] == '有'):
                self.ui.rb_voxel_active.setChecked(True)
            if(config['lane']['rb_selected_related_samples'] == '有'):
                self.ui.rb_related_samples_active.setChecked(True)
            
            if(config['lane']['rb_selected_presence'] == '無'):
                self.ui.rb_presence_disactive.setChecked(True)
            if(config['lane']['rb_selected_stlle_plate'] == '無'):
                self.ui.rb_stlle_plate_disactive.setChecked(True)

            if(config['lane']['sample_type'] == '岩石'):
                self.ui.rb_rock_sample.setChecked(True)
            elif(config['lane']['sample_type'] == '生物'):
                self.ui.rb_bioligical_sample.setChecked(True)
            else:
                self.ui.rb_other_sample.setChecked(True)
            
            self.ui.e_specimen_storage_area.setText(config['lane']['e_specimen_storage_area'])
            self.ui.e_correspondence_of_datasets.setText(config['lane']['e_datasets'])
            self.ui.e_changes_in_voxel_z_width_within_a_same_dataset.setText(config['lane']['e_voxel'])
            self.ui.e_notes.setText(config['lane']['e_note'])
            self.ui.e_detailed_information.setText(config['lane']['e_specimen_storage_area_3'])
            
            if(config['lane']['cb_shatai'] == '0'):
                self.ui.cb_shatai.setChecked(False)
            else:
                self.ui.cb_shatai.setChecked(True)
            
            if("「正のみ」" in self.ui.l_output_volume_huku.text()):
                self.ui.b_output_volume_huku.setDisabled(True)        
                self.ui.rb_sei.setChecked(True)

            elif("「LTOなし」" in self.ui.l_output_volume_sei.text()):
                self.ui.b_output_volume_sei.setDisabled(True)   
                self.ui.b_output_volume_huku.setDisabled(True)   
                self.ui.rb_seifuku_nashi.setChecked(True)
            else:
                self.ui.rb_seifuku.setChecked(True)

            self.textBrowser_output('[EVENT]iniファイルが読み込まれました。')
        
        except:
            pass

        
    def chat_message_send(self,message):

        URL = 'https://api.chatwork.com/v2'
        url = URL + '/rooms/' + self.ui.e_chatwork_room_id.text() + '/messages'
        headers = { 'X-ChatWorkToken': self.ui.e_chatwork_api_key.text() }
        params = { 'body': message }
        try:
            resp = requests.post(url,headers=headers,params=params)
        except:  
           print("チャットワーク送信時にエラーが発生しました")

    def lane_checker(self):
        try:
            self.light_type_names = []
            self.positions = []
            self.temperature_pare = []
            self.voxel_pare = []
            result = False
            if(self.light_pares == []):
                return False
            for i in range(len(self.all_lane_numbers)):
                if(self.all_lane_numbers[i].currentText() == str(['1','2','3'][int(self.ui.bg_lane.checkedId()) * (-1) - 2])):
                    self.light_type_names.append(self.light_pares[int(self.e_lights[i].text())-1])
                    self.positions.append(self.e_position_nos[i].text().zfill(2))
                    self.temperature_pare.append(self.temperatures[int(self.e_lights[i].text())-1])
                    self.voxel_pare.append(self.ui.voxels[int(self.e_lights[i].text())-1])
                    result = True
            return result
        except:
            
            return False
def light_changer(target_text):
    if(target_text == 'PA') or (target_text == 'PB') or (target_text == 'GN6000') or (target_text == 'GN9000')  or (target_text == 'RL6000') or (target_text == 'RL9000') or (target_text == 'RLS') or (target_text == 'RLL'):

        return 'wl'
    elif(target_text == 'HP-365') or (target_text == 'SP365'):

        return 'uv365'

    elif(target_text == 'SP530'):
        return 'uv530'

    elif(target_text == 'SP590'):
        return 'uv590'

    else:
        return ''

if __name__=='__main__':

    if rank == 0:
        app = QApplication(sys.argv)
        w = MyForm()
        w.show()
        sys.exit(app.exec_())
    
    else:
        exit()
        """
        irec_flag = True 
        while True:
            req = comm.irecv(source=0, tag=rank)
            data = req.wait()
            
            if(data["arw_basenames"][int(rank)][0] != ""):
                webbrowser.open(data["keysmith_urls_1"][rank])
                time.sleep(5)

                while True:
                    types = ['tif', 'TIF']
                    tif_files = []
                    
                    for ext in types:
                        tmp_path = os.path.join(data["path"] , 'tmp' + str(rank))
                        paths = os.path.join(tmp_path, '*.{}'.format(ext))
                        tif_files.extend(glob.glob(paths))
                    if((tif_files!=[]) and (os.path.getsize(tif_files[0])!=0)):
                        time.sleep(3)
                        shutil.move(tif_files[0],data["tif_names"][rank])
                        webbrowser.open(data["keysmith_urls_2"][rank])
                        time.sleep(2)
                        break
                    elif((data["tif_names"][rank] == "")):
                        break
                    else:
                        time.sleep(1)
                    
                #ARWをリネーム&移動
                for i in range(data["ACN"]):
                    dist_nas_path = os.path.join(data["path"] , 'tmp' + str(rank) , data["target_paths"][int(rank)][i])
                    dist_nas_file_name = data["arw_basenames"][int(rank)][i]
                    shutil.move(dist_nas_path,dist_nas_file_name)

            else: 	
                irec_flag = False 
            
            req = comm.isend(irec_flag, dest=0, tag=(rank + 10)) 	
            req.wait() 
        """