from bs4 import BeautifulSoup
import requests
import time
import csv
import io
import shutil

def trimString(str):
    if len(str) > 0:
        if str[0] == " ":
            return str[1:]

def cleanString(str):
    str = str.replace("\r", "")
    str = str.replace("\n", "")
    old = ""
    while str != old:
        old = str
        str = str.replace("  ", "")
    return str

def saveImg(url, filename):
    print("\t\tBaixando capa...")
    user_agent = {'User-agent': 'Mozilla/5.0'}
    r = requests.get(url, stream=True, headers = user_agent)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)



def dumpCSV(lib):
    keys = ["Título", "Autores", "Editora", "Idioma", "Tipo de capa",
            "Preço", "Descrição", "Data de publicação", "Número de páginas",
            "Edição", "ISBN-10", "ISBN-13", "ASIN", "Avaliação", "Link", "Categorias",
            "Ranking em Autoajuda", "Comprar Junto 1", "Comprar Junto 2",
            "Comprar Junto 3", "Review 1", "Review 2", "Review 3"]

    try:
        libraryFile = io.open(libraryFilename, "a", newline='', encoding='utf-8')
    except IOError:
        print("Erro ao acessar persistente da biblioteca.")
        return False

    bookwriter = csv.writer(libraryFile, dialect="unix")
    for book in lib:
        entry = []
        for key in keys:
            if book[key] == None:
                book[key] = ""
            entry.append(book[key])
        bookwriter.writerow(entry)
    libraryFile.close()
    return True


def digestSearchResult(addr):

    user_agent = {'User-agent': 'Mozilla/5.0'}
    page = requests.get(addr, headers=user_agent)
    if page.status_code != 200:
        print("\t>>Erro ao obter a página.")
        return False

    soup = BeautifulSoup(page.text, 'html.parser')

    pageTitle = soup.find("title")
    if pageTitle != None and "Serviço não disponível" in pageTitle.contents[0]:
        print("\t>> Erro ao obter a página")
        return False

    resCol = soup.find(id="resultsCol")
    if resCol == None:
        resCol = soup.find(id="mainResults")
    res = resCol.find_all(class_="a-link-normal s-access-detail-page  a-text-normal")
    llist = []
    for i in range(len(res)):
        llist.append(res[i].get("href"))

    return llist


def digestBookPage(addr, num):
    user_agent = {'User-agent': 'Mozilla/5.0'}
    page = requests.get(addr, headers=user_agent)
    if page.status_code != 200:
        print("\t\t>> Erro ao obter a página.")
        return False

    soup = BeautifulSoup(page.text, 'html.parser')

    pageTitle = soup.find("title")
    if pageTitle != None and "Serviço não disponível" in pageTitle.contents[0]:
        print("\t\t>> Erro ao obter a página")
        return False

    titleString=""
    lang=""
    coverType=""
    publishDate=""
    price=""
    description=""
    pages=""
    publisher=""
    edition=""
    isbn10=""
    isbn13=""
    asin=""
    aval=""
    ranking=""
    fbt_list = ["", "", ""]
    reviews=[]
    cats=[]


    res = soup.find_all(id="title")
    if len(res) > 0:
        title = res[0].find(id="productTitle")
        if title == None:
            title = res[0].find(id="ebooksProductTitle")
        if len(title) > 0:
            titleString = title.contents[0]
            infos = res[0].find_all(class_="a-color-secondary")
            if len(infos) == 3:
                lang = infos[0].contents[0]
                coverType = infos[1].contents[0]
                publishDate = infos[2].contents[0]
            elif len(infos) == 2:
                coverType = infos[0].contents[0]
                publishDate = infos[1].contents[0]
            elif len(infos) == 1:
                coverType = infos[0].contents[0]


    authors = []
    res = soup.find_all(class_="author notFaded")
    for entry in res:
        author = entry.find_all("a")
        if len(author) > 0:
            authors.append(author[0].contents[0])
    auths = ", ".join(authors)

    res = soup.find(class_="a-color-price")
    if res != None:
        price=res.contents[0]

    res = soup.find_all("noscript")
    if len(res) >= 1:
        desc = res[1].find("div")
        if desc != None:
            description = ""
            for string in desc.stripped_strings:
                description += string + " "

    if "Itens que você visualizou recentemente e recomendações baseadas em seu histórico recente" in description:
        description = "Descrição não disponível."



    res = soup.find(id="revMHRL")
    if res != None:
        revs = res.find_all("div")
        for div in revs:
            div_id = div.get("id")
            if div_id != None and "rev-dp" in div_id:
                rev_st = div.find_all(class_="a-section")
                stars_st = div.find_all(class_="a-icon-alt")
                for i in range(min(len(stars_st), len(rev_st))):
                    rev_content = "("
                    for string in stars_st[i].stripped_strings:
                        rev_content += string
                    rev_content += ") "
                    for string in rev_st[i].stripped_strings:
                        rev_content += string
                    reviews.append(rev_content)


    res = soup.find(id="detail_bullets_id")
    if res != None:
        itens = res.find_all("li")
    else:
        itens = []
    for item in itens:
        head = item.b.extract()
        if ("Capa comum" in head.contents[0] or "Número de páginas" in head.contents[0] or "Capa dura" in head.contents[0]) and len(item.contents) > 0:
            pages = item.contents[0].replace(" páginas", "")
        elif "Editora" in head.contents[0] and len(item.contents) > 0:
            data = item.contents[0].split(";")
            if len(data) == 1:
                publisher = data[0].split("(")[0]
            elif len(data) > 0:
                publisher = data[0]
            if len(data) > 1:
                edition = data[1].replace("Edição: ", "").replace("ª", "")
        elif "ISBN-10" in head.contents[0] and len(item.contents) > 0:
            isbn10 = item.contents[0]
        elif "ISBN-13" in head.contents[0] and len(item.contents) > 0:
            isbn13 = item.contents[0]
        elif "ASIN" in head.contents[0] and len(item.contents) > 0:
            asin = item.contents[0]
        elif "Idioma" in head.contents[0] and lang == "" and len(item.contents) > 0:
            lang = item.contents[0]

    rating = soup.find(class_="swSprite")
    if rating != None:
        aval = rating.get("title").replace(" de 5 estrelas", "").replace(".", ",")

    stripped_page = page.text.replace("<b>", "")
    stripped_page = stripped_page.replace("</b>", "")
    soup = BeautifulSoup(stripped_page, 'html.parser')

    res = soup.find_all("span", class_="zg_hrsr_ladder")
    res2 = soup.find_all("span", class_="zg_hrsr_rank")
    if res != None and res2 != None:
        for i in range(len(res)):
            cat = ""
            for string in res2[i].stripped_strings:
                cat += string + " "
            cat2 = ""
            for string in res[i].stripped_strings:
                cat2 += string + " "
            cat = cat + cat2
            cat = cat.replace("#", "")
            cats.append(cat)
            if cat2 == "em Livros > Autoajuda ":
                for c in cat:
                    if c != " ":
                        ranking += c
                    else:
                        break
            ranking = ranking.replace("#", "")

    res = soup.find(id="imgBlkFront")
    if res != None:
        imglink = res.get("data-a-dynamic-image").split('"')
        imglink = imglink[1]
    else:
        imglink = "https://pbs.twimg.com/profile_images/600060188872155136/st4Sp6Aw.jpg"
    saveImg(imglink, "images/" + str(num) + ".jpg")

    res = soup.find(id='sims-fbt')
    if res != None:
        fbt_res = res.find_all(class_="sims-fbt-checkbox-label")
        if len(fbt_res) >= 2:
            for i in range(1, len(fbt_res), 1):
                if i-1 > 2:
                    break
                name_link = fbt_res[i].find("a")
                if name_link != None:
                    for string in name_link.stripped_strings:
                        fbt_list[i-1] += string + " "
                    fbt_list[i-1] += "( https://www.amazon.com.br" + name_link.get("href") + " )"

    lang = lang.replace("(", "")
    lang = lang.replace(")", "")

    publishDate = publishDate.replace("– ", "")
    if "fev" in publishDate:
        publishDate = publishDate.replace("fev", "feb")
    elif "abr" in publishDate:
        publishDate = publishDate.replace("abr", "apr")
    elif "mai" in publishDate:
        publishDate = publishDate.replace("mai", "may")
    elif "ago" in publishDate:
        publishDate = publishDate.replace("ago", "aug")
    elif "set" in publishDate:
        publishDate = publishDate.replace("set", "sep")
    elif "out" in publishDate:
        publishDate = publishDate.replace("out", "oct")
    elif "dez" in publishDate:
        publishDate = publishDate.replace("dez", "dec")

    pages = trimString(pages)
    publisher = trimString(publisher)
    edition = trimString(edition)
    isbn10 = trimString(isbn10)
    isbn13 = trimString(isbn13)

    rev_list = ["", "", ""]
    for i in range(len(reviews)):
        if i > 2:
            break
        else:
            rev_list[i] = reviews[i]


    book_obj = {"Título":titleString, "Idioma":lang, "Tipo de capa":coverType,
                "Data de publicação":publishDate, "Autores":auths, "Preço":price,
                "Descrição":description, "Número de páginas":pages, "Editora":publisher,
                "Edição":edition, "ISBN-10":isbn10, "ISBN-13":isbn13, "ASIN":asin,
                "Avaliação":aval, "Ranking em Autoajuda":ranking, "Link":addr,
                "Categorias":", ".join(cats),
                "Comprar Junto 1":fbt_list[0], "Comprar Junto 2":fbt_list[1],
                "Comprar Junto 3":fbt_list[2], "Review 1":rev_list[0],
                "Review 2":rev_list[1], "Review 3":rev_list[2]}

    for key in book_obj:
        if book_obj[key] == None:
            book_obj[key] = ""
        book_obj[key] = cleanString(book_obj[key])

    return book_obj

def getDB(tryCount, booksCount, startPage, endPage):
    searchURL = "https://www.amazon.com.br/s/ref=sr_pg_INDEX?rh=n%3A6740748011%2Cn%3A%217841278011%2Cn%3A7841720011&page=INDEX&ie=UTF8"
    for i in range(startPage,endPage+1,1):
        library = []
        while True:
            print("Obtendo página %d..." %(i))
            url = searchURL.replace("INDEX", str(i))
            try:
                linklist = digestSearchResult(url)
            except:
                print("\tErro ao obter a página %d!!!" %(i))
                linklist = []
            if linklist:
                break
        for j in range(len(linklist)):
            print("\tObtendo livro %d de %d da %da página..." %(j+1, len(linklist), i) )
            cont = 0
            while cont < 10:
                try:
                    book = digestBookPage(linklist[j], booksCount + 1)
                except:
                    print("\t\tErro ao obter o livro %d!!!" %(j+1))
                    book = {"Título":"", "Idioma":"", "Tipo de capa":"",
                                "Data de publicação":"", "Autores":"", "Preço":"",
                                "Descrição":"", "Número de páginas":"", "Editora":"",
                                "Edição":"", "ISBN-10":"", "ISBN-13":"", "ASIN":"",
                                "Avaliação":"", "Ranking em Autoajuda":"", "Link":"",
                                "Categorias":"",
                                "Comprar Junto 1":"", "Comprar Junto 2":"",
                                "Comprar Junto 3":"", "Review 1":"",
                                "Review 2":"", "Review 3":""}
                tryCount+=1
                if book and book["Título"] != "":
                    library.append(book)
                    booksCount+=1
                    break
                else:
                    cont = cont + 1
                print("\t\tRepetindo..." )

        if dumpCSV(library):
            del library
    return tryCount, booksCount

libraryFilename = "lib.csv"
tryCount = 0
booksCount = 0

print(time.strftime("%a, %d/%m/%Y\r\nIniciando busca às %T", time.localtime()))
start = time.time()

tryCount, booksCount = getDB(tryCount, booksCount, 1, 400)

end = time.time()
print(time.strftime("Busca finalizada em %a, %d/%m/%Y, às %T", time.localtime()))
print("Obteve %d livros em %d segundos (%f segundos/livro)" %(booksCount, end-start, (end-start)/booksCount))
print("Taxa de sucesso: %.2f" %(100*booksCount/tryCount))
