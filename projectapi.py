# # try____________________________________________________


# # Generate some data to send to PHP
# #result = {'status': 'Yes!'}

# # Send it to stdout (to PHP)
# #print json.dumps(1)
# # try___________________________________________________

import io
from google.cloud import vision
import re
import nltk
from nltk import sent_tokenize,word_tokenize
from nltk.corpus import wordnet as wn
from pattern.text.en import conjugate, lemma, lexeme,PRESENT,SG
import math
import os
from difflib import SequenceMatcher
import enchant

import sys, json
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"





project_dir = "C:/Users/vigne/Desktop/cip/Subjective-answer-evaluation-modified/"
image_file = project_dir+'a1.png'

client = vision.ImageAnnotatorClient()

def get_marks(data,image_file):

    keywords_matched=0
    #maximum_marks = 5
    maximum_marks = data[0]
    
    keywords=[]
    keywords=data[3].split(',')


    # keywords=['data','mine','database','characterization','knowledge','background','task','classify','associate','visualize','predict','cluster']
    expected_keywords = len(keywords)
    
    #expected_no_of_words = 200
    expected_no_of_words = data[1]
    
    #expected_no_of_sentences = 15
    expected_no_of_sentences = data[2]
    

    print()    
    print("----------------------------------------------")
    print()
    
    spaced_keywords=[]
    for word in keywords:
        if ' ' in word:
            spaced_keywords.append(word)
    for word in spaced_keywords:
        keywords.remove(word)        
    
    print(spaced_keywords)
    print(keywords)


    # extended_keywords = []
    # for word in keywords:
    #     for syn in wn.synsets(word):
    #         for l in syn.lemmas():
    #             extended_keywords.append(l.name())
    
    forms = [] #We'll store the derivational forms in a set to eliminate duplicates
    for word in keywords:
        for alemma in wn.lemmas(word): #for each "alemma" lemma in WordNet
            forms.append(alemma.name()) #add the lemma itself
            for related_lemma in alemma.derivationally_related_forms(): #for each related lemma
                forms.append(related_lemma.name()) #add the related lemma
    
    verb=[]
    for word in keywords:
        verb.extend(lexeme(word))
    
    keywords.extend(forms)
    keywords.extend(verb)
    
    keywords =  [x.lower() for x in keywords]
    keywords = list(set(keywords))
    
    print()
    print("----------------------------------------------")
    print()
    print(keywords)
    print()

    with io.open(image_file, 'rb') as image_file:
        content = image_file.read()
    image = vision.types.Image(content=content)
    
    response = client.text_detection(image=image)
    texts = response.text_annotations
    string = texts[0].description.replace('\n',' ').lower() #for converting to lower case
    string = re.sub('[^A-Za-z0-9.]+', ' ', string) #for eliminating special character

    #here pyenchant is called
    print("-----------------------------------------------")
    print()
    print(string)
    print()

    word_list = word_tokenize(string) #for word spliting
    no_of_words = len(word_list)
    word_list = word_enchant(word_list)


    if no_of_words>expected_no_of_words:
        no_of_words=expected_no_of_words
    
    sent_list = sent_tokenize(string)
   
    print(sent_list)
    print()
    print("------------------------------------------------")
    print()


    no_of_sentences = len(sent_list)
    if no_of_sentences>expected_no_of_sentences:
        no_of_sentences=expected_no_of_sentences

    print('no_of_words:',no_of_words)
    print('no_of_sentences:',no_of_sentences)
    
    list_of_matched_keywords=[]
    for keyword in keywords:
        if(keyword in word_list):
            keywords_matched=keywords_matched+1
            list_of_matched_keywords.append(keyword) 
    for sent in spaced_keywords:
        for sentence in sent_list:
            if sent in sentence:
                keywords_matched=keywords_matched+1
                list_of_matched_keywords.append(sent)  
            else:
                match_ratio = similar(sentence, sent)
                if match_ratio > 0.4:
                    keywords_matched=keywords_matched+1
                    list_of_matched_keywords.append(sent)      
    if keywords_matched>expected_keywords:
        keywords_matched = expected_keywords
    print ('no of keywords matched:',keywords_matched)
    print('keywords matched: ',list_of_matched_keywords)
    
    keywords_percentage = 0.60*(keywords_matched/expected_keywords)    
    word_percentage = 0.30*(no_of_words/expected_no_of_words)
    sentence_percentage = 0.10*(no_of_sentences/expected_no_of_sentences)
    
    print ('keywords_percentage:',keywords_percentage)
    print ('word_percentage:',word_percentage)
    print ('sentence_percentage:',sentence_percentage)
    
    total_marks = maximum_marks*(keywords_percentage+word_percentage+sentence_percentage)
    total_marks=round(total_marks,1)
    digit=total_marks*10
    if(digit%10<5):
        total_marks=math.floor(total_marks)
    if(digit%10>5):
        total_marks=math.ceil(total_marks)  
    print ('total_marks:',total_marks)

    print()
    print("(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)")
    print()
    return total_marks


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def word_enchant(word_list):
    enchanted_list=[]
    enchantable_words=[]
    enchanted_words=[]
    d=enchant.Dict("en_US")
    for word in word_list:
        enchanted_list.append(word)
        if d.check(word) == False:
            enchantable_words.append(word)
            a = set(d.suggest(word))
            max_ratio=0
            proper_word=''
            for b in a:
                tmp = SequenceMatcher(None, word, b).ratio()
                if tmp > max_ratio:
                    proper_word=b
                    max_ratio=tmp
            enchanted_words.append(proper_word)
            enchanted_list.append(proper_word)
    print(enchantable_words)
    print(enchanted_words)
    print()
    return enchanted_list


from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
app = Flask(__name__)
img_directory = app.config['UPLOAD_FOLDER'] = 'uploads/'

app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])


@app.route('/')
def hello_world():
    return render_template('index.html')


marks_disp= {}

@app.route('/result', methods=['POST'])
def get_result():

    #files = request.files['image']
    #print(request.form['keywords'])
    files1 = request.files.getlist('image')
    #print(files1)
    for filess in files1:
        if filess:
            filename = secure_filename(filess.filename)
            filess.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  
            filess = app.config['UPLOAD_FOLDER']+filename          
            #print(filess)
            data = [int(request.form['max_marks']), int(request.form['min_words']), int(request.form['min_sentence']), request.form['keywords']]
            
            print()
            print()
            print("(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)(^-^)")
            print()
            print(filess)
            
            marks = get_marks(data,filess)
            
            size = len(filename)
            if ".png" or ".jpg" in filename:
                filename = filename[:size-4]
            else:
                filename = filename[:size-5] 
            marks_disp[filename] = marks
    
    marks_disp1 = marks_disp.copy()
    marks_disp.clear()
    return render_template("result.html", marks=marks_disp1)        
    
    
    
    
    
    #filename = secure_filename(files.filename)
    #files.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    #files = app.config['UPLOAD_FOLDER']+filename
    #print (files)

    #if files:
        #print(request.form['keywords'])
        #data = [int(request.form['max_marks']), int(request.form['min_words']), int(request.form['min_sentence']), request.form['keywords']]
        
        #marks = get_marks(data,files)
        #return render_template('result.html', marks=marks)
app.run(host='0.0.0.0')


