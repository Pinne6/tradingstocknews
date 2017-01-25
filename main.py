from hubstorage import HubstorageClient
import csv
import datetime
import smtplib
import os
import getopt, sys
import scraping_settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import struct
import imghdr
from InstagramAPI import InstagramAPI
import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import textwrap
from pytz import timezone
import time

# server 'local' o 'remoto'
server = scraping_settings.server
# your email address, the sender
mail_from = scraping_settings.mail_from
# the TO address
mail_to = scraping_settings.mail_to
# your mail username
mail_username = scraping_settings.mail_username
# your mail password
mail_password = scraping_settings.mail_password
# your mail server
mail_server = scraping_settings.mail_server
# your mail port
mail_port = scraping_settings.mail_port
# API key
API = scraping_settings.API
# directory
dir = scraping_settings.dir
yahoo_finance_storico_jobs_csv = scraping_settings.storico_jobs_csv
# modalita di test
test_mode = False
lista = []
storico_jobs = []
apertura_eu = datetime.time(9, 0, 0)
chiusura_eu = datetime.time(17, 30, 0)
apertura_us = datetime.time(15, 30, 0)
chiusura_us = datetime.time(22, 0, 0)
apertura_as = datetime.time(1, 0, 0)
chiusura_as = datetime.time(9, 0, 0)
apertura_me = datetime.time(9, 0, 0)
chiusura_me = datetime.time(19, 30, 0)
apertura_cu = datetime.time(0, 0, 0)
chiusura_cu = datetime.time(23, 59, 59)
lista_indici_eu = ['^FTSE', '^GDAXI', '^FCHI', 'FTSEMIB.MI']  # UK, DE, FR, IT
lista_indici_us = ['^GSPC', '^DJI', '^IXIC']
lista_indici_as = ['^N225', '^HSI', '000001.SS']
lista_metalli = ['GC=F', 'SI=F', 'CL=F', 'BZ=F']  # gold, silver, crude oil, oil
lista_currency = ['EURUSD=X', 'GBPUSD=X', 'EURCHF=X', 'JPY=X', 'EURGBP=X']
titles__super_positive_eu = ['climbs to the top', 'loves green', 'doesn\'t stop']
titles_positive_eu = ['is green', 'is climbing', 'is pointing north']
titles_neutral_eu = ['goes nowhere', 'doesn\'t move', 'feels OK-ish']
titles_negative_eu = ['is red', 'isn\t happy', 'is pointing south']
titles_super_negative_eu = ['goes bananas', 'in free fall', 'down to hell']
titles_default_eu = ['major indices update']
average_super_positive = 1
average_positive = 0.3
average_negative = -0.3
average_super_negative = -1
immagine = dir + '/trading_05_blur.jpg'
footer_sx = ''
footer_dx = '@TradingStockNews'
default_text_color = '#ffffff'
instagram_caption = 'Double tap if you like our updates! Comment below: are you winning today? ' \
                    '#stockmarket #stocktrader #trading #technicalanalysis #stocks #swingtrader #euro #dollar #forex ' \
                    '#forextrading #daytrader #daytrading #trader #binaryoptions #currencytrading #eurusd #usd ' \
                    '#gbpusd #pennystocks #fx #fxtrader #tradingsignals #capital #fxtrading #makemoney #TagsForLikes ' \
                    '#bank #instarich #instagood #money #cash'
instagram_caption = 'test'


def send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject,
               mail_body):
    """
    Invia una mail con tutti i parametri
    :param mail_from:
    :param mail_to:
    :param mail_username:
    :param mail_password:
    :param mail_server:
    :param mail_port:
    :param mail_subject:
    :param mail_body:
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = 'servizio.tappeto@gmail.com'
        msg['To'] = mail_to
        msg['Subject'] = mail_subject
        body = mail_body
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        server.login('servizio.tappeto@gmail.com', 'amicifxt')
        text2 = msg.as_string()
        server.sendmail('servizio.tappeto@gmail.com', mail_to, text2)
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + 'Email inviata con successo')
        server.quit()
    except smtplib.SMTPException:
        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + 'Errore: Problema di invio mail')


def get_quotes():
    if os.path.exists(yahoo_finance_storico_jobs_csv):
        with open(yahoo_finance_storico_jobs_csv) as f:
            for line in f:
                storico_jobs.append(line)
    else:
        mail_subject = "Problema, non trovo file con lo storico jobs"
        mail_body = "Problema, non trovo file con lo storico jobs"
        send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject, mail_body)
        exit()

    hc = HubstorageClient(auth=API)
    # lista dei job, il primo della lista e' l'ultimo eseguito
    run = hc.push_job(projectid='146771', spidername='YahooFinance')
    job = hc.get_job(run.key)
    while job.metadata['state'] != 'finished':
        time.sleep(10)
        job = hc.get_job(run.key)
    items = hc.get_job(run.key).items.list()
    for item in items:
        lista.append((item['simbolo'], item['prezzo'], item['variazione'], item['time_aggiornamento'],
                      item['segno'], item['titolo'], item['percentuale']))
    mail_subject = "Scraping job eseguito"
    mail_body = "Scraping job eseguito " + run.key
    send_email(mail_from, mail_to, mail_username, mail_password, mail_server, mail_port, mail_subject, mail_body)
    with open(yahoo_finance_storico_jobs_csv, 'a', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(run.key)
        f.close()
    return lista


def decide_quotes(lista, args):
    print('dentro decide_quotes')
    out_listini = []
    out_metalli = []
    out_currency = []
    lista_da_pubblicare = []
    if datetime.datetime.today().weekday() < 5 or test_mode:
        # e giorno feriale, lista comprende indici, metalli e currency
        if args[0] == 'currency':
            # currency sono aperte sempre, quindi le aggiungo
            for i in lista:
                if i[0] in lista_currency and i[3].find('At close'):
                    out_currency.append(i)
            lista_da_pubblicare.append('cu')
        # aggiungo gli indici in base agli orari di apertura
        elif args[0] == 'listini':
            print('dentro decide_quotes listini')
            if apertura_eu < datetime.datetime.now().time() < chiusura_eu or test_mode:
                # aggiungo i listini europei
                for i in lista:
                    if i[0] in lista_indici_eu:
                        out_listini.append(i)
                lista_da_pubblicare.append('eu')
            if apertura_us < datetime.datetime.now().time() < chiusura_us or test_mode:
                # aggiungo i listini americani
                for i in lista:
                    if i[0] in lista_indici_us:
                        out_listini.append(i)
                lista_da_pubblicare.append('us')
            if apertura_as < datetime.datetime.now().time() < chiusura_as or test_mode:
                # aggiungo i listini asiatici
                for i in lista:
                    if i[0] in lista_indici_as:
                        out_listini.append(i)
                lista_da_pubblicare.append('as')
            # aggiungo i metalli in base all'orario di apertura
            """
            if apertura_me < datetime.datetime.now().time() < chiusura_me or test_mode:
                # aggiungo i metalli
                for i in lista:
                    if i[0] in lista_metalli:
                        out_metalli.append(i)
                lista_da_pubblicare.append('me') """
        return out_listini, out_metalli, out_currency, lista_da_pubblicare


def create_images(out_listini, out_metalli, out_currency, lista_da_pubblicare, args):
    if args[0] == 'listini' and len(lista_da_pubblicare) == 2:
        print('dentro create_images 2 listini')
        # ho due listini
        # faccio una immagine con listini
        # decido come formattare l'immagine dei listini
        if 'eu' in lista_da_pubblicare and 'us' in lista_da_pubblicare:
            # ho sia EU che US, titolo deve comprendere entrambi
            # per ogni item creo la formattazione adeguata
            testo, rgb = format_text(out_listini)
            # creo il titolo per eu
            listini_eu = [item for item in out_listini if item[0] in lista_indici_eu]
            titolo = create_title(listini_eu)
            titolo = ['EU ' + titolo]
            # creo il titolo per us
            listini_us = [item for item in out_listini if item[0] in lista_indici_us]
            titolo_us = create_title(listini_us)
            titolo.append('US ' + titolo_us)
            footer_sx = create_footer()
            img_output = api_creazione_immagine(testo, rgb, titolo, footer_sx, footer_dx, args)
    elif args[0] == 'listini' and len(lista_da_pubblicare) == 1:
        print('dentro create_images 1 listini')
        if 'eu' in lista_da_pubblicare:
            # ho EU per il titolo
            # per ogni item creo la formattazione adeguata
            testo, rgb = format_text(out_listini)
            # creo il titolo per eu
            listini_eu = [item for item in out_listini if item[0] in lista_indici_eu]
            titolo = create_title(listini_eu)
            titolo = ['EU ' + titolo]
            footer_sx = create_footer()
            img_output = api_creazione_immagine(testo, rgb, titolo, footer_sx, footer_dx, args)
        elif 'us' in lista_da_pubblicare:
            # ho US per il titolo
            # per ogni item creo la formattazione adeguata
            testo, rgb = format_text(out_listini)
            # creo il titolo per eu
            listini_us = [item for item in out_listini if item[0] in lista_indici_us]
            titolo = create_title(listini_us)
            titolo = ['US ' + titolo]
            footer_sx = create_footer()
            img_output = api_creazione_immagine(testo, rgb, titolo, footer_sx, footer_dx, args)
    elif args[0] == 'currency':
        if 'cu' in lista_da_pubblicare:
            # ho currency per il titolo
            # per ogni item creo la formattazione adeguata
            testo, rgb = format_text(out_currency)
            # creo il titolo per currency
            # listini_currency = [item for item in out_currency if item[0] in lista_currency]
            # titolo = create_title(listini_currency)
            titolo = ['FX update']
            footer_sx = create_footer()
            img_output = api_creazione_immagine(testo, rgb, titolo, footer_sx, footer_dx, args)
    return img_output


def api_creazione_immagine(testo, rgb, titolo, footer_sx, footer_dx, args):
    img = Image.open(immagine)
    width, height = img.size
    draw = ImageDraw.Draw(img)
    # font = ImageFont.truetype(<font-file>, <font-size>)
    font = ImageFont.truetype(dir + "/LemonMilk.otf", 90)
    # draw.text((x, y),"Sample Text",(r,g,b))
    current_h = 50
    pad = 20
    for item in titolo:
        w, h = draw.textsize(item, font=font)
        draw.text(((width - w) / 2, current_h), item, default_text_color, font=font)
        current_h += h + pad
    font = ImageFont.truetype(dir + "/LemonMilk.otf", 50)
    i = 0
    for item in testo:
        # il primo elemento e il nome titolo, il secondo il valore, il terzo la variazione
        # il nome titolo lo allineo a sinistra
        w, h = font.getsize(item[0])
        draw.text((70, 350 + (100 * i)), item[0], default_text_color, font=font)
        # il valore lo allineo a destra
        w, h = font.getsize(item[1])
        if args[0] == 'listini':
            draw.text((600 - w, 350 + (100 * i)), item[1], default_text_color, font=font)
        elif args[0] == 'currency':
            draw.text((500 - w, 350 + (100 * i)), item[1], default_text_color, font=font)
        # la variazione la allineo a destra
        w, h = font.getsize(item[2])
        draw.text((1040 - w, 350 + (100 * i)), item[2], rgb[i], font=font)
        i += 1
    font = ImageFont.truetype(dir + "/LemonMilk.otf", 20)
    draw.text((10, 1040), footer_sx, '#ffffff', font=font)
    draw.text((800, 1040), footer_dx, '#ffffff', font=font)
    img_output = dir + '/instagram_output.jpg'
    img.save(img_output)
    return img_output


def create_footer():
    ora_eu = datetime.datetime.utcnow().strftime('%H:%M')
    eastern = timezone('US/Eastern')
    ora_us = datetime.datetime.now(eastern).strftime('%H:%M')
    footer = "Last update " + ora_eu + " GMT / " + ora_us + " EST"
    return footer


def create_title(input_list):
    # calcolo la media dei positivi
    media = sum(float(item[6]) for item in input_list) / len(input_list)
    if media >= average_super_positive:
        title = titles_super_positive_eu[random.randint(0, len(titles_super_positive_eu) - 1)]
    elif average_positive <= media < average_super_positive:
        title = titles_positive_eu[random.randint(0, len(titles_positive_eu) - 1)]
    elif average_negative < media < average_positive:
        title = titles_neutral_eu[random.randint(0, len(titles_neutral_eu) - 1)]
    elif average_super_negative < media <= average_negative:
        title = titles_negative_eu[random.randint(0, len(titles_negative_eu) - 1)]
    elif media <= average_super_negative:
        title = titles_super_negative_eu[random.randint(0, len(titles_super_negative_eu) - 1)]
    else:
        title = titles_default_eu[random.randint(0, len(titles_default_eu) - 1)]
    return title


def format_text(text):
    linee = len(text)
    text_out = []
    rgb = []
    for i, item in enumerate(text):
        if item[0] == 'FTSEMIB.MI':
            nome = 'FTSE MIB'
        elif item[0] == '^DJI':
            nome = 'Dow Jones'
        elif item[0] == '^IXIC':
            nome = 'NASDAQ'
        elif item[0] == '^N225':
            nome = 'Nikkei'
        elif item[0] == '^HSI':
            nome = 'Hang Seng'
        elif item[0] == '000001.SS':
            nome = 'Shanghai'
        elif item[0] == 'GC=F':
            nome = 'Gold Future'
        elif item[0] == 'SI=F':
            nome = 'Silver Future'
        elif item[0] == 'CL=F':
            nome = 'Crude Oil'
        elif item[0] == 'BZ=F':
            nome = 'Brent Oil'
        else:
            nome = item[5]
        text_out.append((nome, item[1], item[2]))
        if item[4] == 'green':
            rgb.append('#00ff00')
        else:
            rgb.append('#ff0000')
    return text_out, rgb


def publish_instagram(image, instagram_caption):
    instagram_api = InstagramAPI("tradingstocknews", "sto23espo")
    instagram_api.login()  # login
    instagram_api.uploadPhoto(image, instagram_caption)
    instagram_api.logout()
    return


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "output="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err))  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        else:
            assert False, "unhandled option"
    # recupero gli ultimi prezzi
    if args[0] != 'listini' and args[0] != 'currency':
        print('errore')
        exit()
    if not test_mode:
        lista = get_quotes()
    else:
        lista = [('DAX', '11,630.13', '+33.24 (+0.29%)', 'At close: 5:36PM CET', 'green', '^GDAXI', '+0.29'),
                 ('CAC 40', '4850.37', '-9.53 (-0.20%)', 'At close: 5:36PM CET', 'red', '^FCHI', '-0.20'),
                 ('DOW JONES', '4850.37', '-9.53 (-0.20%)', 'At close: 5:36PM CET', 'red', '^DJI', '-0.20')]
    # decido quali quote far vedere in base all'ora del giorno
    out_listini, out_metalli, out_currency, lista_da_pubblicare = decide_quotes(lista, args)
    image = create_images(out_listini, out_metalli, out_currency, lista_da_pubblicare, args)
    instagram_caption = 'test'
    print('sono a stampare instagram')
    publish_instagram(image, instagram_caption)
    exit()

if __name__ == "__main__":
    main()
"""
    MAIN LOOP
    1- ricevo le quote da scrapy
    2- decido quali quotes tenere in base a giorno e orario
    3- creo immagine in base ai listini presenti
    4- pubblico su instagram
"""