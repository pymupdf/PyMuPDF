import fitz
import json

my_json =  """
[
    {
         "name" :           "Five-storied Pagoda",
         "temple" :         "Rurikō-ji",
         "founded" :        "middle Muromachi period, 1442",
         "region" :         "Yamaguchi, Yamaguchi",
         "position" :       "34.190181,131.472917"
     },
     {
         "name" :           "Founder's Hall",
         "temple" :         "Eihō-ji",
         "founded" :        "early Muromachi period",
         "region" :         "Tajimi, Gifu",
         "position" :       "35.346144,137.129189"
     },
     {
         "name" :           "Fudōdō",
         "temple" :         "Kongōbu-ji",
         "founded" :        "early Kamakura period",
         "region" :         "Kōya, Wakayama",
         "position" :       "34.213103,135.580397"
     },
     {
         "name" :           "Goeidō",
         "temple" :         "Nishi Honganji",
         "founded" :        "Edo period, 1636",
         "region" :         "Kyoto",
         "position" :       "34.991394,135.751689"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Murō-ji",
         "founded" :        "early Heian period",
         "region" :         "Uda, Nara",
         "position" :       "34.536586819357986,136.0395548452301"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Fudō-in",
         "founded" :        "late Muromachi period, 1540",
         "region" :         "Hiroshima",
         "position" :       "34.427014,132.471117"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Ninna-ji",
         "founded" :        "Momoyama period, 1613",
         "region" :         "Kyoto",
         "position" :       "35.031078,135.713811"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Mii-dera",
         "founded" :        "Momoyama period, 1599",
         "region" :         "Ōtsu, Shiga",
         "position" :       "35.013403,135.852861"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Tōshōdai-ji",
         "founded" :        "Nara period, 8th century",
         "region" :         "Nara, Nara",
         "position" :       "34.675619,135.784842"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Tō-ji",
         "founded" :        "Momoyama period, 1603",
         "region" :         "Kyoto",
         "position" :       "34.980367,135.747686"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Tōdai-ji",
         "founded" :        "middle Edo period, 1705",
         "region" :         "Nara, Nara",
         "position" :       "34.688992,135.839822"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Hōryū-ji",
         "founded" :        "Asuka period, by 693",
         "region" :         "Ikaruga, Nara",
         "position" :       "34.614317,135.734458"
     },
     {
         "name" :           "Golden Hall",
         "temple" :         "Daigo-ji",
         "founded" :        "late Heian period",
         "region" :         "Kyoto",
         "position" :       "34.951481,135.821747"
     },
     {
         "name" :           "Keigū-in Main Hall",
         "temple" :         "Kōryū-ji",
         "founded" :        "early Kamakura period, before 1251",
         "region" :         "Kyoto",
         "position" :       "35.015028,135.705425"
     },
     {
         "name" :           "Konpon-chūdō",
         "temple" :         "Enryaku-ji",
         "founded" :        "early Edo period, 1640",
         "region" :         "Ōtsu, Shiga",
         "position" :       "35.070456,135.840942"
     },
     {
         "name" :           "Korō",
         "temple" :         "Tōshōdai-ji",
         "founded" :        "early Kamakura period, 1240",
         "region" :         "Nara, Nara",
         "position" :       "34.675847,135.785069"
     },
     {
         "name" :           "Kōfūzō",
         "temple" :         "Hōryū-ji",
         "founded" :        "early Heian period",
         "region" :         "Ikaruga, Nara",
         "position" :       "34.614439,135.735428"
     },
     {
         "name" :           "Large Lecture Hall",
         "temple" :         "Hōryū-ji",
         "founded" :        "middle Heian period, 990",
         "region" :         "Ikaruga, Nara",
         "position" :       "34.614783,135.734175"
     },
     {
         "name" :           "Lecture Hall",
         "temple" :         "Zuiryū-ji",
         "founded" :        "early Edo period, 1655",
         "region" :         "Takaoka, Toyama",
         "position" :       "36.735689,137.010019"
     },
     {
         "name" :           "Lecture Hall",
         "temple" :         "Tōshōdai-ji",
         "founded" :        "Nara period, 763",
         "region" :         "Nara, Nara",
         "position" :       "34.675933,135.784842"
     },
     {
         "name" :           "Lotus Flower Gate",
         "temple" :         "Tō-ji",
         "founded" :        "early Kamakura period",
         "region" :         "Kyoto",
         "position" :       "34.980678,135.746314"
     },
     {
         "name" :           "Main Hall",
         "temple" :         "Akishinodera",
         "founded" :        "early Kamakura period",
         "region" :         "Nara, Nara",
         "position" :       "34.703769,135.776189"
     }
]

"""

# the result is a Python dictionary:
my_dict = json.loads(my_json)

MEDIABOX = fitz.paper_rect("letter")  # output page format: Letter
WHERE = MEDIABOX + (36, 36, -36, -36)
writer = fitz.DocumentWriter("json-example.pdf")  # create the writer

story = fitz.Story()
body = story.body

for i, entry in enumerate(my_dict):

    for attribute, value in entry.items():
        para = body.add_paragraph()

        if attribute == "position":
            para.set_fontsize(10)
            para.add_link(f"www.google.com/maps/@{value},14z")
        else:
            para.add_span()
            para.set_color("#990000")
            para.set_fontsize(14)
            para.set_bold()
            para.add_text(f"{attribute} ")
            para.add_span()
            para.set_fontsize(18)
            para.add_text(f"{value}")

    body.add_horizontal_line()

# This while condition will check a value from the Story `place` method
# for whether all content for the story has been written (0), otherwise
# more content is waiting to be written (1)
more = 1
while more:
    device = writer.begin_page(MEDIABOX)  # make new page
    more, _ = story.place(WHERE)
    story.draw(device)
    writer.end_page()  # finish page

writer.close()  # close output file

del story
