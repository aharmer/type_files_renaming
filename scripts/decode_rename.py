import os
import sys
from pathlib import Path
import shutil
import glob
import re
import cv2
import numpy as np
import pylibdmtx.pylibdmtx as dmtx
from pyzbar.pyzbar import decode

# Function to decode datamatrix
def decode_datamatrix(frame):
  
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7,7))
    closing = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        if cv2.contourArea(contour) > 1000:  # Adjust the threshold based on your needs
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h

            # Check if the aspect ratio is close to 1 (square shape)
            if 0.8 <= aspect_ratio <= 1.2:
                pts = contour.reshape(-1, 2)
                rect = cv2.minAreaRect(pts)
                box = cv2.boxPoints(rect)
                box = box.astype(int)
                cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)

                # Crop the detected DataMatrix region
                roi = gray[y - 5:y + h + 5, x - 5:x + w + 5]

                # Decode the DataMatrix
                try:
                    decoded_data = dmtx.decode(roi)
                    for data in decoded_data:
                        print('Datamatrix successfuly decoded: ', data.data.decode('utf-8'))
                        return data.data.decode('utf-8')  # Return the decoded data
                except dmtx.PyLibDMTXError:
                    continue

    return None


# Function to decode 1D barcode
def decode_barcode(frame):
  
    detected_barcodes = decode(frame)

    min_width = 10  # Minimum width threshold for barcode region
    min_height = 10  # Minimum height threshold for barcode region
    
    if not detected_barcodes:
        raise Exception(print('No barcodes were detected...'))
    else:
        for barcode in detected_barcodes:
            (x, y, w, h) = barcode.rect
            
            if w > min_width and h > min_height:
                cv2.rectangle(frame, (x-10, y-10), (x + w+10, y + h+10), (0, 255, 0), 2)
                if barcode.data != "":
                    print('Barcode successfuly decoded: ', barcode.data.decode('utf-8'))
                    return barcode.data.decode('utf-8')


def decoder(in_path):
  
    img = cv2.imread(in_path)

    try:
        print('\nTrying barcode decoder on file...', in_path)
        decoded_data = decode_barcode(img)
    except:
        print('Trying datamatrix decoder...')
        decoded_data = decode_datamatrix(img)
        
    return decoded_data     
    

def main():
  
    if len(sys.argv) != 3:
        raise Exception('Unexpected number of inputs.\n'
            'Example: python decode_rename.py input_dir output_dir')

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    print('\nSource files:', in_path)
    print('Output destination:', out_path)
    
    file_names = glob.glob(in_path + '/*.tif*')
    spp_names = []
    for h, file in enumerate(file_names):
      spp = re.split("_", os.path.basename(file))[:1]
      spp_names.append(spp)
    print('\nList of species:')
    for id in np.unique(spp_names):
      print(id)
      
    failed_attempts = []
    for i, filename in enumerate(glob.glob(in_path + '/*lbl*')):
      try:
        assc_no = decoder(filename)
        
        for j, sp in enumerate(np.unique(spp_names)):
          if sp == re.split("_", os.path.basename(filename))[:1][0]:
            check = np.isin(np.array(spp_names), sp).all(1)
            idx = np.where(np.array(check) == True)
            for k in list((0,1)):
              old_name = file_names[idx[0][k]]
              new_name = out_path + assc_no + '_' + os.path.basename(old_name)
              shutil.copy(old_name, new_name)
              print('File successfully renamed as...', new_name)
  
      except:
        failed_attempts.append(filename)
        print('Unable to decode data in label file.')

    print('\nFollowing label files could not be decoded, rename these manually:')
    for f in failed_attempts:
        print(f)


    ### For visualisation
    
    # frame = cv2.imread("")
  
    # try:
    #     print('Trying barcode decoder...')
    #     decoded_data = decode_barcode(frame)
    # except:
    #     print('Trying datamatrix decoder...')
    #     decoded_data = decode_datamatrix(frame)

    # if decoded_data:
    #     cv2.putText(frame, "Decoded Data: " + decoded_data, (5, 25), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 1, cv2.LINE_AA)
    #         
    # cv2.namedWindow("Decoded", cv2.WINDOW_NORMAL)
    # cv2.imshow('Decoded', frame)
    # cv2.waitKey(0)


if __name__ == '__main__':
    main()

