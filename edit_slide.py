from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from pdf2image import convert_from_path
import os
import subprocess

ORIKAESHI_LENGTH = 60

def create_caption(taxon_lithology,geological_age,locality,specimen_number,nas_path,light_source,target_tif_number,mov_name,horizon,fov,voxel,image_pixel_width,fov_w,position,frame_change,name,isItaric,camera_name,same_time_mode):
    # ファイルの指定
    if(same_time_mode == False):
        image_number = specimen_number + "_" + light_source + "_" + position + "_" + target_tif_number
    else:
        image_number = specimen_number + "_" + light_source + "_" + position + "_NNNN"

    print(image_number)
    template_file = r'template/template_pdf.pdf' # 既存のテンプレートPDF
    template_file = os.path.join(os.getcwd() , template_file)

    tmp_file = r'template/__tmp.pdf' # 一時ファイル
    tmp_file = os.path.join(os.getcwd() , tmp_file)

    output_file = r'template/caption_pdf.pdf'
    output_file = os.path.join(os.getcwd() , output_file)
    
    img_name = r'template/caption_img.jpg'
    img_name = os.path.join(os.getcwd() , img_name)

    cv = canvas.Canvas(tmp_file, pagesize=(9051, 6034)) #ページサイズの単位はピクセル→(1149mm,766mm)
    centor = 100
    space = 80
    font_size = 60
    font_big = 80

    cv.setFillColorRGB(255,255,255) #choose your font colour 
    ttf_file = os.path.join(os.getcwd() , 'template/fonts/Roboto/Roboto-Regular.ttf')
    pdfmetrics.registerFont(TTFont('ARIAL', ttf_file))
    cv.setFont('ARIAL', font_size)

    cv.drawString(centor, 1800 - space, 'Spec no:')  #1
    ttf_file = os.path.join(os.getcwd() , 'template/fonts/Roboto/Roboto-Bold.ttf')
    pdfmetrics.registerFont(TTFont('ARIALBD', ttf_file))
    cv.setFont('ARIALBD', font_big)
    cv.drawString(350, 1800 - space, specimen_number)  #1

    ttf_file = os.path.join(os.getcwd() , 'template/fonts/Roboto/Roboto-Regular.ttf')
    pdfmetrics.registerFont(TTFont('ARIAL', ttf_file))
    cv.setFont('ARIAL', font_size)
    cv.drawString(centor, 1800 - (space*2), 'Image no: ' + image_number) #2
    cv.drawString(centor,1800 - (space*4), 'Name:')              #3
    
    ttf_file = os.path.join(os.getcwd() , 'template/fonts/Roboto/Roboto-Bold.ttf')
    pdfmetrics.registerFont(TTFont('ARIALBD', ttf_file))
    cv.setFont('ARIALBD', font_big)

    if(isItaric == True):
        ttf_file = os.path.join(os.getcwd() , 'template/fonts/Roboto/Roboto-Bolditalic.ttf')
        pdfmetrics.registerFont(TTFont('ARIALBI', ttf_file))
        cv.setFont('ARIALBI', font_big)
    
    cv.drawString(centor + 200, 1800 - (space*4),name)            #3
  
    ttf_file = os.path.join(os.getcwd() , 'template/fonts/Roboto/Roboto-Bold.ttf')
    pdfmetrics.registerFont(TTFont('ARIAL', ttf_file))
    cv.setFont('ARIAL', font_size)
    

    if(taxon_lithology == "Taxon and/or lithology"):                #4
        cv.drawString(centor, 1800 - (space*5), 'Age: ' + geological_age)

    occurrence_offcet = 0

    #文字列置換
    if(taxon_lithology == "Taxon and/or lithology") or (taxon_lithology == "Binominal name"):
        if("Formation" in horizon):
            horizon = horizon.replace("Formation","Fm.")
        if("Group" in horizon):
            horizon = horizon.replace("Group","Gp.")

    #文字列の折り返しが必要かチェック    #5
    if(len(horizon + "," + locality)<ORIKAESHI_LENGTH):
        cv.drawString(centor, 1800 - (space*6), 'Occurrence: ' + horizon + ", " + locality)

    elif(len(horizon) > ORIKAESHI_LENGTH) and (len(locality) > ORIKAESHI_LENGTH):#horizon localityの双方が90文字以上の場合
        occurrence_offcet = space*3
        cv.drawString(centor, 1800 - (space*6), 'Occurrence: ' + horizon[:ORIKAESHI_LENGTH])
        cv.drawString(centor, 1800 - (space*7), horizon[ORIKAESHI_LENGTH:] + ", ")
        cv.drawString(centor, 1800 - (space*8), locality[:ORIKAESHI_LENGTH])
        cv.drawString(centor, 1800 - (space*9), locality[ORIKAESHI_LENGTH:])

    elif(len(horizon) > ORIKAESHI_LENGTH) and (len(locality) <= ORIKAESHI_LENGTH):#horizonのみ90文字以上の場合
        occurrence_offcet = space*2
        cv.drawString(centor, 1800 - (space*6), 'Occurrence: ' + horizon[:ORIKAESHI_LENGTH])
        cv.drawString(centor, 1800 - (space*7), horizon[ORIKAESHI_LENGTH:]+ ", ")
        cv.drawString(centor, 1800 - (space*8), locality)

    elif(len(horizon) <= ORIKAESHI_LENGTH) and (len(locality) > ORIKAESHI_LENGTH):#localityのみ90文字以上の場合
        occurrence_offcet = space*1
        cv.drawString(centor, 1800 - (space*6), 'Occurrence: ' + horizon+ ", ")
        cv.drawString(centor, 1800 - (space*7), locality[:ORIKAESHI_LENGTH])
        cv.drawString(centor, 1800 - (space*8), locality[ORIKAESHI_LENGTH:])


    cv.drawString(centor,  1800 - (space*8) - occurrence_offcet, 'Original dimensions of images: ' + image_pixel_width)           #6

    if(fov != 'error') and (fov!="") and (voxel != ""): #7
        cv.drawString(centor, 1800 - (space*9) - occurrence_offcet, 'Voxel size (x, y axis/ z axis): '+ fov +'(μm/pixel) / '+ str(voxel) +' (μm/slice: ' + str(target_tif_number) + ')' )
    else:
        occurrence_offcet = occurrence_offcet -space
    
    if(fov_w != ""):
        cv.drawString(centor, 1800 - (space*10) - occurrence_offcet, 'Original image width: ' + fov_w + '(mm)')     #8
    else:
        occurrence_offcet = occurrence_offcet -space

    if("GFX 100s" in camera_name):
        cv.drawString(centor, 1800 - (space*11) - occurrence_offcet, 'Animation: 4344x3258 pixel, 15 frames/sec.') #10
    else:
        cv.drawString(centor, 1800 - (space*11) - occurrence_offcet, 'Animation: 4344x2896 pixel, 15 frames/sec.') #10
    
    if(light_source == "uv365"):
        cv.drawString(centor, 1800 - (space*13) - occurrence_offcet, 'Note: Under UV light (wavelength: 365 nm).')    #9
    
    cv.showPage()
    cv.save()

    template_pdf = PdfFileReader(template_file)
    template_page = template_pdf.getPage(0)

    tmp_pdf = PdfFileReader(tmp_file)
    template_page.mergePage(tmp_pdf.getPage(0))

    output = PdfFileWriter()
    output.addPage(template_page)

    with open(output_file, "wb") as fp:
        output.write(fp)

    images = convert_from_path(output_file)
    images[0].save(img_name, 'jpeg')

    if(frame_change == True):
        subprocess.call('ffmpeg -y -loglevel quiet -loop 1 -i ' + img_name + ' -vcodec mjpeg -pix_fmt yuv420p -b:v 600000000000000 -t 2 -r 15 -s 4344x3258 ' + mov_name,shell=True)
    else:
        subprocess.call('ffmpeg -y -loglevel quiet -loop 1 -i ' + img_name + ' -vcodec mjpeg -pix_fmt yuv420p -b:v 600000000000000 -t 2 -r 15 -s 4344x2896 ' + mov_name,shell=True)

    return mov_name
