import argparse
from glob import glob
from os.path import basename

import cv2 as cv
from tesserocr import PSM
from tesserocr import PyTessBaseAPI


def image_to_text(filename, lang, psm):
    with PyTessBaseAPI(lang=lang, psm=psm) as api:
        # api.SetImage(self.image)
        api.SetImageFile(filename)
        text = api.GetUTF8Text()
        return text.strip()


def ocr(filename):
    image = cv.imread(filename)
    orig = image.copy()
    height, width, _channels = orig.shape

    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    cv.imwrite('gray.jpg', gray)
    ret, thresh = cv.threshold(gray, 120, 255, cv.THRESH_BINARY_INV)
    # cleaned = thresh.copy()
    cv.imwrite('thresh.jpg', thresh)
    # thresh = cv.bitwise_not(thresh)
    # print(thresh)

    # cnts = cv.findContours(dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    # cnts, hier = cv.findContours(dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    # kernel = cv.getStructuringElement(cv.MORPH_RECT, (20, 5))
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (20, 1))
    # kernel = np.ones((10, 10), np.uint8)
    dilate = cv.dilate(thresh, kernel, iterations=3)
    cv.imwrite('dilate.jpg', dilate)
    cnts, hier = cv.findContours(dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    # cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    # print(len(cnts), cnts)
    contours = []
    for c in cnts:
        x, y, w, h = cv.boundingRect(c)
        # print(x, y, w, h)
        if h < 10:
            continue
        contours.append(c)
        # break
    # sort by y
    contours = list(sorted(contours, key=lambda c: cv.boundingRect(c)[1]))[:3]
    contours = list(sorted(contours, key=lambda c: cv.boundingRect(c)[0]))
    # for c in contours:
    #     print(cv.boundingRect(c))
    # print(contours)

    img_contours = orig.copy()
    cv.drawContours(img_contours, contours, -1, (255, 0, 255), 2)
    cv.imwrite('contours.jpg', img_contours)

    # contours = contours[:3]
    assert len(contours) == 3, 'Expected 3 contours, got {}'.format(len(contours))
    contours = [contours[0], contours[2]]
    lines = [basename(filename)]
    for i, c in enumerate(contours):
        x, y, w, h = cv.boundingRect(c)
        margin = 2
        x = max(0, x-margin)
        y = max(0, y-margin)
        w = min(width, w + margin * 2)
        h = min(height, h + margin * 2)
        cropped = orig[y:y + h, x:x + w]
        cv.imwrite('cropped{}.png'.format(i), cropped)
        cv.imwrite('cropped.png', cropped)
        text = image_to_text('cropped.png', 'nor', PSM.SINGLE_BLOCK)
        lines.append(text)
        cv.rectangle(image, (x, y), (x + w, y + h), (255, 0, 255), 2)
    print(','.join(lines))
    # cv.drawContours(image, contours, -1, (0,255,0), 3)
    cv.imwrite('image.jpg', image)
    # print('contur', c)
    #     # cv.drawContours(dilate, [c], -1, (0, 0, 0), -1)
    #     cv.rectangle(image, (x, y), (x + w, y + h), (255, 0, 255), 2)

    # result = 255 - cv.bitwise_and(dilate, mask)
    #
    # cv.imshow('mask', mask)
    # cv.imshow('dilate', dilate)
    # cv.imshow('result', result)
    # cv.imshow('gray', gray)
    # cv.imshow('thresh', thresh)
    # cv.imshow('dilate', dilate)
    # cv.imshow('image', image)
    cv.waitKey(0)


def ocr2(filename):
    img = cv.imread(filename)

    img_final = cv.imread(filename)
    img2gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, mask = cv.threshold(img2gray, 180, 255, cv.THRESH_BINARY)
    image_final = cv.bitwise_and(img2gray, img2gray, mask=mask)
    ret, new_img = cv.threshold(image_final, 180, 255, cv.THRESH_BINARY)  # for black text , cv.THRESH_BINARY_INV
    '''
            line  8 to 12  : Remove noisy portion
    '''
    kernel = cv.getStructuringElement(cv.MORPH_CROSS, (3,
                                                       3))  # to manipulate the orientation of dilution , large x means horizonatally dilating  more, large y means vertically dilating more
    dilated = cv.dilate(new_img, kernel, iterations=9)  # dilate , more the iteration more the dilation

    # for cv.x.x

    # _, contours, hierarchy = cv.findContours(dilated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)  # findContours returns 3 variables for getting contours

    # for cv3.x.x comment above line and uncomment line below

    # image, contours, hierarchy = cv.findContours(dilated,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    # cnts = cv.findContours(dilated,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)
    cnts = cv.findContours(dilated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    for contour in cnts:
        # get rectangle bounding contour
        [x, y, w, h] = cv.boundingRect(contour)
        print(x, y, w, h)

        # Don't plot small false positives that aren't text
        # if w < 35 and h < 35:
        #     continue

        # draw rectangle around contour on original image
        cv.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 2)

        '''
        #you can crop image and send to OCR  , false detected will return no text :)
        cropped = img_final[y :y +  h , x : x + w]

        s = file_name + '/crop_' + str(index) + '.jpg'
        cv.imwrite(s , cropped)
        index = index + 1

        '''
    # write original image with added contours to disk
    cv.imshow('captcha_result', img)
    cv.waitKey()


def main():
    parser = argparse.ArgumentParser(
        description='Calculate weight of the images in a directory')
    parser.add_argument('--input', help='path to the image')
    args = parser.parse_args()

    for filename in sorted(glob(args.input)):
        ocr(filename)


if __name__ == "__main__":
    main()
