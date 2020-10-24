
import io
from google.cloud import vision
import re
import nltk
from nltk import sent_tokenize,word_tokenize
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from pattern.text.en import conjugate, lemma, lexeme,PRESENT,SG
import math
import os
from difflib import SequenceMatcher
import enchant

import sys, json
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

import sqlite3
from sqlite3 import Error

import smtplib



app = Flask(__name__)



project_dir = "C:/Users/vigne/Desktop/cip/Subjective-answer-evaluation-modified/"
image_file = project_dir+'a1.png'

client = vision.ImageAnnotatorClient()

def get_marks(data,image_file):

    keywords_matched=0
    #maximum_marks = 5
    maximum_marks = data[0]
    
    keywords=[]
    keywords=data[3].copy()


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
    image_file.close()
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


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def select_all_data(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM student_mail")
    rows = cur.fetchall()
    print(rows)
    return rows

MY_ADDRESS = 'vigneshsivamani2206@gmail.com'
PASSWORD = 'rocketleague'

def send_emails(rows,marks_disp):
    message = """From:<vigneshsivamani2206@gmail.com>
    To:<{email}>
    Subject: SMTP Marks

    You have scored {marks} marks.
    """
    
    for (rollno,name,mail) in rows:
        s = smtplib.SMTP('smtp.gmail.com',587)
        s.starttls()
        s.login(MY_ADDRESS,PASSWORD)
        txt = message.format(email=mail,marks=marks_disp[name])
        s.sendmail(MY_ADDRESS, mail, txt) 
        #print(txt)
        s.quit()
    




img_directory = app.config['UPLOAD_FOLDER'] = 'uploads/'
img_directory1 = app.config['UPLOAD_FOLDERS'] = 'uploadss/'

app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])

@app.route('/')
def hello_world():
    return render_template('index.html')


marks_disp= {}

@app.route('/result', methods=['POST'])
def get_result():

    files1 = request.files.getlist('image')
    #print(files1)
    keywordss=request.form['keywords'].split(',')
    
    counter=0
    a_words=0
    a_sents=0
    total_text=''
    for filesss in files1:
        if filesss:
            filename = secure_filename(filesss.filename)
            #filesss.save(os.path.join(app.config['UPLOAD_FOLDERS'], filename))  
            filesss = app.config['UPLOAD_FOLDERS']+filename
            
            with io.open(filesss, 'rb') as image_file:
                content = image_file.read()
            image = vision.types.Image(content=content)
    
            response = client.text_detection(image=image)
            texts = response.text_annotations
            strings = texts[0].description.replace('\n',' ').lower() #for converting to lower case
            strings = re.sub('[^A-Za-z0-9.]+', ' ', strings) #for eliminating special character 
            total_text= total_text+strings
            #strings = getstring(filesss)
            list1 = word_tokenize(strings)
            list2 = sent_tokenize(strings)
            a_words=a_words+len(list1)
            a_sents=a_sents+len(list2)
            counter=counter+1

    text_tokens = word_tokenize(total_text)
    tokens_without_sw = [word for word in text_tokens if not word in stopwords.words()]
    pos_tagged_words=nltk.pos_tag(tokens_without_sw)
    needed_words_tag=[(word,pos) for (word,pos) in pos_tagged_words if pos=='NN' or pos=='NNP' or pos=='NNS' or pos=='NNPS' or pos=='VB' or pos=='VBN' or pos=='VBP' or pos=='VBZ' or pos=='VBD' or pos=='VBG']
    needed_words=[word for (word,pos) in needed_words_tag]
    fdist1 = nltk.FreqDist(needed_words)
    fdist2=fdist1.most_common(5)
    print()
    print("-------start of session--------")
    print()
    print (fdist2)

    for (word,count) in fdist2:
        if word not in keywordss:
            print()
            print(word,count)
            val = int(input("Enter your choice: 1 to consider the word as a keyword or 0 to leave it:"))
            if val==1:
                keywordss.append(word)


    print()
    print(keywordss)
    print()
    #print(needed_words)
    
    a_words=a_words/counter
    a_sents=a_sents/counter

    e_words=int(request.form['min_words'])
    e_sents=int(request.form['min_sentence'])

    print("which to consider:")
    print("expected no of words is:",e_words)
    print("average no of words is:",int(a_words))
    val = int(input("Enter your choice: 1 for expected 0 for average: "))
    if val==1:
        a_words=int(e_words)
    else:
        a_words=int(a_words)
    
    print("\nwhich to consider:")
    print("expected no of sentences is:",e_sents)
    print("average no of sentences is:",int(a_sents))
    val = int(input("Enter your choice: 1 for expected 0 for average: "))
    if val==1:
        a_sents=int(e_sents)
    else:
        a_sents=int(a_sents)



    
    
    for filess in files1:
        if filess:
            filename = secure_filename(filess.filename)
            filess.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  
            filess = app.config['UPLOAD_FOLDER']+filename          
            #print(filess)
            
            data = [int(request.form['max_marks']), a_words, a_sents, keywordss]
            
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


    conn = create_connection(r"C:\sqlite\db\studentmail.db")
    with conn:
        print("querrying details")
        print()
        rows = select_all_data(conn)
    
    send_emails(rows,marks_disp1)

    print()
    print("----------end of session------------")


    marks_disp.clear()
    return render_template("result.html", marks=marks_disp1)        
app.run(host='0.0.0.0')


