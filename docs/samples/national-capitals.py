"""
Demo script using (Py-) MuPDF "Story" feature.

The following features are implemented:

* Use of Story "template" feature to provide row content
* Use database access (SQLITE) to fetch row content
* Use ElementPosition feature to locate cell positions on page
* Simulate feature "Table Header Repeat"
* Simulate feature "Cell Grid Lines"

"""
import io
import sqlite3
import sys

import fitz

"""
Table data. Used to populate a temporary SQL database, which will be processed by the script.
Its only purpose is to avoid carrying around a separate database file.
"""
table_data = """China;Beijing;21542000;1.5%;2018
Japan;Tokyo;13921000;11.2%;2019
DR Congo;Kinshasa;12691000;13.2%;2017
Russia;Moscow;12655050;8.7%;2021
Indonesia;Jakarta;10562088;3.9%;2020
Egypt;Cairo;10107125;9.3%;2022
South Korea;Seoul;9508451;18.3%;2022
Mexico;Mexico City;9209944;7.3%;2020
United Kingdom;London;9002488;13.4%;2020
Bangladesh;Dhaka;8906039;5.3%;2011
Peru;Lima;8852000;26.3%;2012
Iran;Tehran;8693706;9.9%;2016
Thailand;Bangkok;8305218;11.6%;2010
Vietnam;Hanoi;8053663;8.3%;2019
Iraq;Baghdad;7682136;17.6%;2021
Saudi Arabia;Riyadh;7676654;21.4%;2018
Hong Kong;Hong Kong;7291600;100%;2022
Colombia;Bogotá;7181469;13.9%;2011
Chile;Santiago;6310000;32.4%;2012
Turkey;Ankara;5747325;6.8%;2021
Singapore;Singapore;5453600;91.8%;2021
Afghanistan;Kabul;4601789;11.5%;2021
Kenya;Nairobi;4397073;8.3%;2019
Jordan;Amman;4061150;36.4%;2021
Algeria;Algiers;3915811;8.9%;2011
Germany;Berlin;3677472;4.4%;2021
Spain;Madrid;3305408;7.0%;2021
Ethiopia;Addis Ababa;3040740;2.5%;2012
Kuwait;Kuwait City;2989000;70.3%;2018
Guatemala;Guatemala City;2934841;16.7%;2020
South Africa;Pretoria;2921488;4.9%;2011
Ukraine;Kyiv;2920873;6.7%;2021
Argentina;Buenos Aires;2891082;6.4%;2010
North Korea;Pyongyang;2870000;11.1%;2016
Uzbekistan;Tashkent;2860600;8.4%;2022
Italy;Rome;2761632;4.7%;2022
Ecuador;Quito;2800388;15.7%;2020
Cameroon;Yaoundé;2765568;10.2%;2015
Zambia;Lusaka;2731696;14.0%;2020
Sudan;Khartoum;2682431;5.9%;2012
Brazil;Brasília;2648532;1.2%;2012
Taiwan;Taipei (de facto);2608332;10.9%;2020
Yemen;Sanaa;2575347;7.8%;2012
Angola;Luanda;2571861;7.5%;2020
Burkina Faso;Ouagadougou;2453496;11.1%;2019
Ghana;Accra;2388000;7.3%;2017
Somalia;Mogadishu;2388000;14.0%;2021
Azerbaijan;Baku;2303100;22.3%;2022
Cambodia;Phnom Penh;2281951;13.8%;2019
Venezuela;Caracas;2245744;8.0%;2016
France;Paris;2139907;3.3%;2022
Cuba;Havana;2132183;18.9%;2020
Zimbabwe;Harare;2123132;13.3%;2012
Syria;Damascus;2079000;9.7%;2019
Belarus;Minsk;1996553;20.8%;2022
Austria;Vienna;1962779;22.0%;2022
Poland;Warsaw;1863056;4.9%;2021
Philippines;Manila;1846513;1.6%;2020
Mali;Bamako;1809106;8.3%;2009
Malaysia;Kuala Lumpur;1782500;5.3%;2019
Romania;Bucharest;1716983;8.9%;2021
Hungary;Budapest;1706851;17.6%;2022
Congo;Brazzaville;1696392;29.1%;2015
Serbia;Belgrade;1688667;23.1%;2021
Uganda;Kampala;1680600;3.7%;2019
Guinea;Conakry;1660973;12.3%;2014
Mongolia;Ulaanbaatar;1466125;43.8%;2020
Honduras;Tegucigalpa;1444085;14.0%;2021
Senegal;Dakar;1438725;8.5%;2021
Niger;Niamey;1334984;5.3%;2020
Uruguay;Montevideo;1319108;38.5%;2011
Bulgaria;Sofia;1307439;19.0%;2021
Oman;Muscat;1294101;28.6%;2021
Czech Republic;Prague;1275406;12.1%;2022
Madagascar;Antananarivo;1275207;4.4%;2018
Kazakhstan;Astana;1239900;6.5%;2022
Nigeria;Abuja;1235880;0.6%;2011
Georgia;Tbilisi;1201769;32.0%;2022
Mauritania;Nouakchott;1195600;25.9%;2019
Qatar;Doha;1186023;44.1%;2020
Libya;Tripoli;1170000;17.4%;2019
Myanmar;Naypyidaw;1160242;2.2%;2014
Rwanda;Kigali;1132686;8.4%;2012
Mozambique;Maputo;1124988;3.5%;2020
Dominican Republic;Santo Domingo;1111838;10.0%;2010
Armenia;Yerevan;1096100;39.3%;2021
Kyrgyzstan;Bishkek;1074075;16.5%;2021
Sierra Leone;Freetown;1055964;12.5%;2015
Nicaragua;Managua;1055247;15.4%;2020
Canada;Ottawa;1017449;2.7%;2021
Pakistan;Islamabad;1014825;0.4%;2017
Liberia;Monrovia;1010970;19.5%;2008
United Arab Emirates;Abu Dhabi;1010092;10.8%;2020
Malawi;Lilongwe;989318;5.0%;2018
Haiti;Port-au-Prince;987310;8.6%;2015
Sweden;Stockholm;978770;9.4%;2021
Eritrea;Asmara;963000;26.6%;2020
Israel;Jerusalem;936425;10.5%;2019
Laos;Vientiane;927724;12.5%;2019
Chad;N'Djamena;916000;5.3%;2009
Netherlands;Amsterdam;905234;5.2%;2022
Central African Republic;Bangui;889231;16.3%;2020
Panama;Panama City;880691;20.2%;2013
Tajikistan;Dushanbe;863400;8.9%;2020
Nepal;Kathmandu;845767;2.8%;2021
Togo;Lomé;837437;9.7%;2010
Turkmenistan;Ashgabat;791000;12.5%;2017
Moldova;Chişinău;779300;25.5%;2019
Croatia;Zagreb;769944;19.0%;2021
Gabon;Libreville;703904;30.1%;2013
Norway;Oslo;697010;12.9%;2021
Macau;Macau;671900;97.9%;2022
United States;Washington D.C.;670050;0.2%;2021
Jamaica;Kingston;662491;23.4%;2019
Finland;Helsinki;658864;11.9%;2021
Tunisia;Tunis;638845;5.2%;2014
Denmark;Copenhagen;638117;10.9%;2021
Greece;Athens;637798;6.1%;2021
Latvia;Riga;605802;32.3%;2021
Djibouti;Djibouti (city);604013;54.6%;2012
Ireland;Dublin;588233;11.8%;2022
Morocco;Rabat;577827;1.6%;2014
Lithuania;Vilnius;576195;20.7%;2022
El Salvador;San Salvador;570459;9.0%;2019
Albania;Tirana;557422;19.5%;2011
North Macedonia;Skopje;544086;25.9%;2015
South Sudan;Juba;525953;4.9%;2017
Paraguay;Asunción;521559;7.8%;2020
Portugal;Lisbon;509614;5.0%;2020
Guinea-Bissau;Bissau;492004;23.9%;2015
Slovakia;Bratislava;440948;8.1%;2020
Estonia;Tallinn;438341;33.0%;2021
Australia;Canberra;431380;1.7%;2020
Namibia;Windhoek;431000;17.0%;2020
Tanzania;Dodoma;410956;0.6%;2012
Papua New Guinea;Port Moresby;364145;3.7%;2011
Ivory Coast;Yamoussoukro;361893;1.3%;2020
Lebanon;Beirut;361366;6.5%;2014
Bolivia;Sucre;360544;3.0%;2022
Puerto Rico (US);San Juan;342259;10.5%;2020
Costa Rica;San José;342188;6.6%;2018
Lesotho;Maseru;330760;14.5%;2016
Cyprus;Nicosia;326739;26.3%;2016
Equatorial Guinea;Malabo;297000;18.2%;2018
Slovenia;Ljubljana;285604;13.5%;2021
East Timor;Dili;277279;21.0%;2015
Bosnia and Herzegovina;Sarajevo;275524;8.4%;2013
Bahamas;Nassau;274400;67.3%;2016
Botswana;Gaborone;273602;10.6%;2020
Benin;Porto-Novo;264320;2.0%;2013
Suriname;Paramaribo;240924;39.3%;2012
India;New Delhi;249998;0.0%;2011
Sahrawi Arab Democratic Republic;Laayoune (claimed) - Tifariti (de facto);217732 - 3000;—;2014
New Zealand;Wellington;217000;4.2%;2021
Bahrain;Manama;200000;13.7%;2020
Kosovo;Pristina;198897;12.0%;2011
Montenegro;Podgorica;190488;30.3%;2020
Belgium;Brussels;187686;1.6%;2022
Cape Verde;Praia;159050;27.1%;2017
Mauritius;Port Louis;147066;11.3%;2018
Curaçao (Netherlands);Willemstad;136660;71.8%;2011
Burundi;Gitega;135467;1.1%;2020
Switzerland;Bern (de facto);134591;1.5%;2020
Transnistria;Tiraspol;133807;38.5%;2015
Maldives;Malé;133412;25.6%;2014
Iceland;Reykjavík;133262;36.0%;2021
Luxembourg;Luxembourg City;124509;19.5%;2021
Guyana;Georgetown;118363;14.7%;2012
Bhutan;Thimphu;114551;14.7%;2017
Comoros;Moroni;111326;13.5%;2016
Barbados;Bridgetown;110000;39.1%;2014
Sri Lanka;Sri Jayawardenepura Kotte;107925;0.5%;2012
Brunei;Bandar Seri Begawan;100700;22.6%;2007
Eswatini;Mbabane;94874;8.0%;2010
New Caledonia (France);Nouméa;94285;32.8%;2019
Fiji;Suva;93970;10.2%;2017
Solomon Islands;Honiara;92344;13.0%;2021
Republic of Artsakh;Stepanakert;75000;62.5%;2021
Gambia;Banjul;73000;2.8%;2013
São Tomé and Príncipe;São Tomé;71868;32.2%;2015
Kiribati;Tarawa;70480;54.7%;2020
Vanuatu;Port Vila;51437;16.1%;2016
Northern Mariana Islands (USA);Saipan;47565;96.1%;2017
Samoa;Apia;41611;19.0%;2021
Palestine;Ramallah (de facto);38998;0.8%;2017
Monaco;Monaco;38350;104.5%;2020
Jersey (UK);Saint Helier;37540;34.2%;2018
Trinidad and Tobago;Port of Spain;37074;2.4%;2011
Cayman Islands (UK);George Town;34399;50.5%;2021
Gibraltar (UK);Gibraltar;34003;104.1%;2020
Grenada;St. George's;33734;27.1%;2012
Aruba (Netherlands);Oranjestad;28294;26.6%;2010
Isle of Man (UK);Douglas;27938;33.2%;2011
Marshall Islands;Majuro;27797;66.1%;2011
Tonga;Nukuʻalofa;27600;26.0%;2022
Seychelles;Victoria;26450;24.8%;2010
French Polynesia (France);Papeete;26926;8.9%;2017
Andorra;Andorra la Vella;22873;28.9%;2022
Faroe Islands (Denmark);Tórshavn;22738;43.0%;2022
Antigua and Barbuda;St. John's;22219;23.8%;2011
Belize;Belmopan;20621;5.2%;2016
Saint Lucia;Castries;20000;11.1%;2013
Guernsey (UK);Saint Peter Port;18958;30.1%;2019
Greenland (Denmark);Nuuk;18800;33.4%;2021
Dominica;Roseau;14725;20.3%;2011
Saint Kitts and Nevis;Basseterre;14000;29.4%;2018
Saint Vincent and the Grenadines;Kingstown;12909;12.4%;2012
British Virgin Islands (UK);Road Town;12603;40.5%;2012
Åland (Finland);Mariehamn;11736;39.0%;2021
U.S. Virgin Islands (US);Charlotte Amalie;14477;14.5%;2020
Micronesia;Palikir;6647;5.9%;2010
Tuvalu;Funafuti;6320;56.4%;2017
Malta;Valletta;5827;1.1%;2019
Liechtenstein;Vaduz;5774;14.8%;2021
Saint Pierre and Miquelon (France);Saint-Pierre;5394;91.7%;2019
Cook Islands (NZ);Avarua;4906;28.9%;2016
San Marino;City of San Marino;4061;12.0%;2021
Turks and Caicos Islands (UK);Cockburn Town;3720;8.2%;2016
American Samoa (USA);Pago Pago;3656;8.1%;2010
Saint Martin (France);Marigot;3229;10.1%;2017
Saint Barthélemy (France);Gustavia;2615;24.1%;2010
Falkland Islands (UK);Stanley;2460;65.4%;2016
Svalbard (Norway);Longyearbyen;2417;82.2%;2020
Sint Maarten (Netherlands);Philipsburg;1894;4.3%;2011
Christmas Island (Australia);Flying Fish Cove;1599;86.8%;2016
Anguilla (UK);The Valley;1067;6.8%;2011
Guam (US);Hagåtña;1051;0.6%;2010
Wallis and Futuna (France);Mata Utu;1029;8.9%;2018
Bermuda (UK);Hamilton;854;1.3%;2016
Nauru;Yaren (de facto);747;6.0%;2011
Saint Helena (UK);Jamestown;629;11.6%;2016
Niue (NZ);Alofi;597;30.8%;2017
Tokelau (NZ);Atafu;541;29.3%;2016
Vatican City;Vatican City (city-state);453;100%;2019
Montserrat (UK);Brades (de facto) - Plymouth (de jure);449 - 0;-;2011
Norfolk Island (Australia);Kingston;341;-;2015
Palau;Ngerulmud;271;1.5%;2010
Cocos (Keeling) Islands (Australia);West Island;134;24.6%;2011
Pitcairn Islands (UK);Adamstown;40;100.0%;2021
South Georgia and the South Sandwich Islands (UK);King Edward Point;22;73.3%;2018"""

# -------------------------------------------------------------------
# HTML template for the report. We define no table header <th> items
# because this is done in post processing.
# The actual template part is the table row, identified by id "row".
# The content of each cell will be filled using the respective id.
# -------------------------------------------------------------------
HTML = """
    <h1 style="text-align:center">World Capital Cities</h1>
    <p><i>Percent "%" is city population as a percentage of the country, as of "Year".</i>
    </p><p></p>
    <table>
    <tr id="row">
        <td id="country"></td>
        <td id="capital"></td>
        <td id="population"></td>
        <td id="percent"></td>
        <td id="year"></td>
    </tr>
    </table>
"""

# -------------------------------------------------------------------
# Sets font-family globally to sans-serif, and text-align to right
# for the numerical table columns.
# -------------------------------------------------------------------
CSS = """
body {
    font-family: sans-serif;
}
td[id="population"], td[id="percent"], td[id="year"] {
    text-align: right;
    padding-right: 2px;
}"""

# -------------------------------------------------------------------
# recorder function for cell positions
# -------------------------------------------------------------------
coords = {}  # stores cell gridline coordinates


def recorder(elpos):
    """We only record positions of table rows and cells.

    Information is stored in "coords" with page number as key.
    """
    global coords  # dictionary of row and cell coordinates per page
    if elpos.open_close != 2:  # only consider coordinates provided at "close"
        return
    if elpos.id not in ("row", "country", "capital", "population", "percent", "year"):
        return  # only look at row / cell content

    rect = fitz.Rect(elpos.rect)  # cell rectangle
    if rect.y1 > elpos.filled:  # ignore stuff below the filled rectangle
        return

    # per page, we store the floats top-most y, right-most x, column left
    # and row bottom borders.
    x, y, x1, y0 = coords.get(elpos.page, (set(), set(), 0, sys.maxsize))

    if elpos.id != "row":
        x.add(rect.x0)  # add cell left border coordinate
        if rect.x1 > x1:  # store right-most cell border on page
            x1 = rect.x1
    else:
        y.add(rect.y1)  # add row bottom border coordinate
        if rect.y0 < y0:  # store top-most cell border per page
            y0 = rect.y0

    coords[elpos.page] = (x, y, x1, y0)  # write back info per page
    return


# -------------------------------------------------------------------
# define database access: make an intermediate memory database for
# our demo purposes.
# -------------------------------------------------------------------
dbfilename = ":memory:"  # the SQLITE database file name
database = sqlite3.connect(dbfilename)  # open database
cursor = database.cursor()  # multi-purpose database cursor

# Define and fill the SQLITE database
cursor.execute(
    """CREATE TABLE capitals (Country text, Capital text, Population text, Percent text, Year text)"""
)

for value in table_data.splitlines():
    cursor.execute("INSERT INTO capitals VALUES (?,?,?,?,?)", value.split(";"))

# select statement for the rows - let SQL also sort it for us
select = """SELECT * FROM capitals ORDER BY "Country" """

# -------------------------------------------------------------------
# define the HTML Story and fill it with database data
# -------------------------------------------------------------------
story = fitz.Story(HTML, user_css=CSS)
body = story.body  # access the HTML body detail

template = body.find(None, "id", "row")  # find the template part
table = body.find("table", None, None)  # find start of table

# read the rows from the database and put them all in one Python list
# NOTE: instead, we might fetch rows one by one (advisable for large volumes)

cursor.execute(select)  # execute cursor, and ...
rows = cursor.fetchall()  # read out what was found
database.close()  # no longer needed

for country, capital, population, percent, year in rows:  # iterate through the row
    row = template.clone()  # clone the template to report each row
    row.find(None, "id", "country").add_text(country)
    row.find(None, "id", "capital").add_text(capital)
    row.find(None, "id", "population").add_text(population)
    row.find(None, "id", "percent").add_text(percent)
    row.find(None, "id", "year").add_text(year)

    table.append_child(row)

template.remove()  # remove the template

# -------------------------------------------------------------------
# generate the PDF and write it to memory
# -------------------------------------------------------------------
fp = io.BytesIO()
writer = fitz.DocumentWriter(fp)
mediabox = fitz.paper_rect("letter")  # use pages in Letter format
where = mediabox + (36, 36, -36, -72)  # leave page borders
more = True
page = 0
while more:
    dev = writer.begin_page(mediabox)  # make a new page
    if page > 0:  # leave room above the cells for inserting header row
        delta = (0, 20, 0, 0)
    else:
        delta = (0, 0, 0, 0)
    more, filled = story.place(where + delta)  # arrange content on this rectangle
    story.element_positions(recorder, {"page": page, "filled": where.y1})
    story.draw(dev)  # write content to page
    writer.end_page()  # finish the page
    page += 1
writer.close()  # close the PDF

# -------------------------------------------------------------------
# re-open memory PDF for inserting gridlines and header rows
# -------------------------------------------------------------------
doc = fitz.open("pdf", fp)
for page in doc:
    page.wrap_contents()  # ensure all "cm" commands are properly wrapped
    x, y, x1, y0 = coords[page.number]  # read coordinates of the page
    x = sorted(list(x)) + [x1]  # list of cell left-right borders
    y = [y0] + sorted(list(y))  # list of cell top-bottom borders
    shape = page.new_shape()  # make a canvas to draw upon

    for item in y:  # draw horizontal lines (one under each row)
        shape.draw_line((x[0] - 2, item), (x[-1] + 2, item))

    for i in range(len(y)):  # alternating row coloring
        if i % 2:
            rect = (x[0] - 2, y[i - 1], x[-1] + 2, y[i])
            shape.draw_rect(rect)

    for i in range(len(x)):  # draw vertical lines
        d = 2 if i == len(x) - 1 else -2
        shape.draw_line((x[i] + d, y[0]), (x[i] + d, y[-1]))

    # Write header row above table content
    y0 -= 5  # bottom coord for header row text
    shape.insert_text((x[0], y0), "Country", fontname="hebo", fontsize=12)
    shape.insert_text((x[1], y0), "Capital", fontname="hebo", fontsize=12)
    shape.insert_text((x[2], y0), "Population", fontname="hebo", fontsize=12)
    shape.insert_text((x[3], y0), "  %", fontname="hebo", fontsize=12)
    shape.insert_text((x[4], y0), "Year", fontname="hebo", fontsize=12)

    # Write page footer
    y0 = page.rect.height - 50  # top coordinate of footer bbox
    bbox = fitz.Rect(0, y0, page.rect.width, y0 + 20)  # footer bbox
    page.insert_textbox(
        bbox,
        f"World Capital Cities, Page {page.number+1} of {doc.page_count}",
        align=fitz.TEXT_ALIGN_CENTER,
    )
    shape.finish(width=0.3, color=0.5, fill=0.9)  # rectangles and gray lines
    shape.commit(overlay=False)  # put the drawings in background

doc.subset_fonts()
doc.save(__file__.replace(".py", ".pdf"), deflate=True, garbage=4, pretty=True)
doc.close()
