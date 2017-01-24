import sys
import cv2

from tools import mkdir_p
from tools import eprint


def binarize(img):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img_gray, 180, 255, cv2.THRESH_BINARY)
    final = cv2.bitwise_and(img_gray, img_gray, mask=mask)
    ret, new = cv2.threshold(final, 180, 255, cv2.THRESH_BINARY)
    return new

def small_block(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return not (w < 200 or h < 50)

def small_word(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return not (h < 5) #(w < 8 or h < 8)

def small_line(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return not (w < 8 or h < 5)

def area(contour):
    #cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)
    return w * h

def contour_y(contour):
    #cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)
    return y

#def mass(img, contour):
def mass(img):
    #x, y, w, h = cv2.boundingRect(contour)
    #line_img = img[y:y+h, x:x+w]
    #ret2,th2 = cv2.threshold(line_img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img_gray.copy(), 180, 255, cv2.THRESH_BINARY)
    return ((255 - mask) > 0).sum()

def word_count(img, contour, line_index):
    x, y, w, h = cv2.boundingRect(contour)
    block_img = img[y:y+h, x:x+w]
    new = binarize(block_img)

    # Find words
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 5))
    dilated = cv2.erode(new.copy(), kernel, iterations=2)

    #cv2.imwrite('line%d.png' % line_index, dilated)
    a, contours, b = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = filter(small_word, contours)

    for contour in contours:
        wx, wy, ww, wh = cv2.boundingRect(contour)
        cv2.rectangle(block_img, (wx, wy), (wx+ww, wy+wh), (0, 120, 0), 1)

    return len(contours)


#def find_text_block(input_name, output_name, dilated_name):
#def find_text_block(input_img):
def find_text_block(input_name):
    img = cv2.imread(input_name)
    #img = cv2.imread('orig-page.png')
    #img = input_img.copy()
    new = binarize(img)
    # img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # ret, mask = cv2.threshold(img_gray, 180, 255, cv2.THRESH_BINARY)
    # final = cv2.bitwise_and(img_gray, img_gray, mask=mask)
    # ret, new = cv2.threshold(final, 180, 255, cv2.THRESH_BINARY)
    #cv2.imwrite('/tmp/dilated.png', new)
    #cv2.waitKey(0)
    #return new, img
    #new = cv2.bitwise_not(new)

    #kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 7))
    #dilated = cv2.dilate(new, kernel, iterations=3)
    dilated = cv2.erode(new.copy(), kernel, iterations=3)

    #contours, hierarchy = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    a, contours, b = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #contours, hierarchy = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #if cv2.__version__.startswith('3.'):
    #    a, contours, b = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #else:
    #    contours, hierarchy = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #from ipdb import set_trace; set_trace()
    contours = filter(small_block, contours)
    contours = sorted(contours, key=area)
    #contours = contours[:-1]
    # index = 0
    print('-' * 10)
    for contour in contours:
        #print(cv2.contourArea(contour))
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 255), 2)

    #cv2.imshow('result.png', dilated)
    #cv2.imwrite('result.png', dilated)

    #cv2.imwrite(dilated_name, dilated)
    #cv2.imwrite(output_name, img)
    #cv2.waitKey()
    return dilated, img, contours

def find_lines_in_block(input_name, contour, block_index, page_index):

    img = cv2.imread(input_name)
    x, y, w, h = cv2.boundingRect(contour)

    block_img = img[y:y+h, x:x+w]
    orig_block_img = block_img.copy()
    new = binarize(block_img)
    #return new

    # Find lines
    #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6, 2))
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (8, 1))
    #dilated = cv2.dilate(new, kernel, iterations=3)
    dilated = cv2.erode(new.copy(), kernel, iterations=2)

    a, contours, b = cv2.findContours(cv2.bitwise_not(dilated.copy()), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = filter(small_line, contours)
    contours = sorted(contours, key=contour_y)

    print('-' * 10)
    for line_index, contour in enumerate(contours):
        c_area = area(contour)
        lx, ly, lw, lh = cv2.boundingRect(contour)
        line_img = orig_block_img[ly:ly+lh, lx:lx+lw]
        fiber_img = orig_block_img[ly+lh/2:ly+lh/2+1, lx:lx+lw]

        line_mass = mass(line_img)
        fiber_mass = mass(fiber_img)
        #c_mass = mass(orig_block_img, contour)

        filename = 'lines/page%03d_block%03d_line%03d.png' % (page_index, block_index, line_index)
        cv2.imwrite(filename, line_img)
        w_count = word_count(block_img, contour, line_index)

        print(line_index,
              'width', lw,
              'height', lh,
              'word_count', w_count,
              'word_count/width', round(float(w_count)/lw, 6),
              'contourArea', cv2.contourArea(contour),
              'area', c_area,
              'mass', line_mass,
              'mass/aria', round(float(line_mass)/c_area, 2),
              'fiber_mass/line_width', round(float(fiber_mass)/lw, 6))

        eprint('%s,%s,%s,%s,%s,%s,%s,%s' % (
            filename, float(line_mass)/c_area,
            float(fiber_mass)/lw, lh, lw, c_area,
            float(w_count)/lw,
            line_index))

        cv2.rectangle(block_img, (lx, ly+lh/2), (lx+lw, ly+lh/2), (250, 0, 0), 1)
        #cv2.putText(block_img, str(line_index), (lx, ly+lh/2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 255, 2)

    # Line Features:
    # - mass/aria (ink_volume)
    # - height
    # - word_count/width (words_ratio)

    return block_img

    #cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 255), 2)

if __name__ == '__main__':
    mkdir_p('lines')
    mkdir_p('blocks')
    eprint('filename,ink_volume,fiber_ink_volume,height,width,area,words_ratio,line_index')
    #find_text_block(sys.argv[1], 'marked.png', 'dilated.png')
    for page_index, page_name in enumerate(sys.argv[1:]):
        print('Page %d' % page_index)
        dilated, img, contours = find_text_block(page_name)
        #dilated, img = find_text_block(cv2.imread(sys.argv[1]),
        #                               cv2.imread('marked.png'),
        #                               cv2.imread('dilated.png'))

        cv2.imwrite('dilated%d.png' % page_index, dilated)
        cv2.imwrite('blocks%d.png' % page_index, img)

        #lines = find_lines_in_block('blocks.png', contours)
        for block_index, contour in enumerate(contours):
            print('Contour %d' % block_index)
            block = find_lines_in_block(page_name, contour, block_index, page_index)
            cv2.imwrite('blocks/page%03d_block%03d.png' % (page_index, block_index), block)
