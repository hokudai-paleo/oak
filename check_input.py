def is_true(self,target,str):
    if target:
            return False
    else:
        self.flag = False
        self.ui.textBrowser.append(str)
        self.ui.textBrowser_2.append(str)
        return True

def default_necessary(self):
    self.flag = True
    if(self.ui.l_input_volume.text() == "not selected"):
        red = is_true(self,False,"Input")
    else:
        red = is_true(self,True,"Output")

    if(red == True):
        self.ui.l_input_volume.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_input_volume.setStyleSheet("QLabel { color : black; }")

    if(self.ui.l_output_volume_sei.text() == "not selected"):
        red = is_true(self,False,"Output (primary)")
    else:
        red = is_true(self,True,"Output(primary)")

    if(red == True):
        self.ui.l_output_volume_sei.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_output_volume_sei.setStyleSheet("QLabel { color : black; }")

    if(self.ui.l_output_volume_huku.text() == "not selected"):
        red = is_true(self,False,"Output (duplicate)")
    else:
        red = is_true(self,True,"Output (duplicate)")

    if(red == True):
        self.ui.l_output_volume_huku.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_output_volume_huku.setStyleSheet("QLabel { color : black; }")


    #General
    red = is_true(self,self.ui.e_digital_specimen_number.text(),"Digital specimen number")
    if(red == True):
        self.ui.l_digital_specimen_number.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_digital_specimen_number.setStyleSheet("QLabel { color : black; }")
        

    red = is_true(self,self.ui.e_analyst.text(),"Name of analyst")
    if(red == True):
        self.ui.l_analyst.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_analyst.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_iso.text(),"ISO")
    if(red == True):
        self.ui.l_iso.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_iso.setStyleSheet("QLabel { color : black; }")
    
    #分析の撮影設定
    red = is_true(self,self.ui.e_total_grinding_thickness_in_each_cycle.text(),"Total grinding thickness in each cycle (μm)")
    if(red == True):
        self.ui.l_total_grinding_thickness_in_each_cycle.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_total_grinding_thickness_in_each_cycle.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_total_grinding_thickness_in_each_finishing_process.text(),"Finishing thickenss(μm)")
    if(red == True):
        self.ui.l_total_grinding_thickness_in_each_finishing_process.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_total_grinding_thickness_in_each_finishing_process.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_depth_of_cut_in_rough_grinding.text(),"Rough grinding thickness (μm)")
    if(red == True):
        self.ui.l_depth_of_cut_in_rough_grinding.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_depth_of_cut_in_rough_grinding.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_depth_of_cut_in_finish_grinding.text(),"Fine grinding thickenss (μm)")
    if(red == True):
        self.ui.l_depth_of_cut_in_finish_grinding.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_depth_of_cut_in_finish_grinding.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_rough_grinding_speed.text(),"Processing speed (mm/min)")
    if(red == True):
        self.ui.l_rough_grinding_speed.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_rough_grinding_speed.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_finish_grinding_speed.text(),"Finishing speed (mm/min)")
    if(red == True):
        self.ui.l_finish_grinding_speed.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_finish_grinding_speed.setStyleSheet("QLabel { color : black; }")

    red = is_true(self,self.ui.e_polishing.text(),"Sparkout (times)")
    if(red == True):
        self.ui.l_polishing.setStyleSheet("QLabel { color : red; }")
    else:
        self.ui.l_polishing.setStyleSheet("QLabel { color : black; }")


    return self.flag

def special_necessary(self,selected):
    if(selected == "Geology and Paleonotlogy"):
        red = is_true(self,self.ui.e_taxon_lithology.text(),'Rock/fossil name')
        if(red == True):
            self.ui.l_taxon_lithology.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_taxon_lithology.setStyleSheet("QLabel { color : black; }")

        red = is_true(self,self.ui.e_geological_age.text(),'Geologic age')
        if(red == True):
            self.ui.l_geological_age.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_geological_age.setStyleSheet("QLabel { color : black; }")
        red = is_true(self,self.ui.e_horizon.text(),"Horizon")
        if(red == True):
            self.ui.l_horizon.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_horizon.setStyleSheet("QLabel { color : black; }")

        red = is_true(self,self.ui.e_locality.text(),'Locality')
        if(red == True):
            self.ui.l_locality.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_locality.setStyleSheet("QLabel { color : black; }")

        

    if(selected == "Biology"):
        red = is_true(self,self.ui.e_taxon_lithology.text(),'Scientific name')
        if(red == True):
            self.ui.l_taxon_lithology.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_taxon_lithology.setStyleSheet("QLabel { color : black; }")

        red = is_true(self,self.ui.e_age.text(),'Age')
        if(red == True):
            self.ui.l_age.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_age.setStyleSheet("QLabel { color : black; }")

        red = is_true(self,self.ui.e_sex.text(),'Age')
        if(red == True):
            self.ui.l_sex.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_sex.setStyleSheet("QLabel { color : black; }")

        red = is_true(self,self.ui.e_strage_condition.text(),'Preservation method')
        if(red == True):
            self.ui.l_strage_condition.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_strage_condition.setStyleSheet("QLabel { color : black; }")

    if(selected == "Others"):
        red = is_true(self,self.ui.e_taxon_lithology.text(),'Sample name')
        if(red == True):
            self.ui.l_taxon_lithology.setStyleSheet("QLabel { color : red; }")
        else:
            self.ui.l_taxon_lithology.setStyleSheet("QLabel { color : black; }")

    return self.flag
    

def shooting_list_checker(self):

    result = True
    for i in range(len(self.all_lane_numbers)):
        if(self.all_lane_numbers[i].currentText() == ''):
            pass
        else:
            red = is_true(self,self.e_lights[i].text(),"Light: row" + str(i+1) + " ")
            if(red == True):
                result = False
            
            red = is_true(self,self.e_position_nos[i].text(),"Capture position: row" + str(i+1) + " ")
            if(red == True):
                result = False
                
    return result