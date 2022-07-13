import fitz


snark = (
        "<!DOCTYPE html>"
        "<style>"
        "#a { margin: 30px; }"
        "#b { margin: 20px; }"
        "#c { margin: 5px; }"
        "#a { border: 1px solid red; }"
        "#b { border: 1px solid green; }"
        "#c { border: 1px solid blue; }"
        "</style>"
        "<body>"
        "<div id=\"a\">"
        "A"
        "</div>"
        "<div id=\"b\">"
        "<div id=\"c\">"
        "C"
        "</div>"
        "</div>"
        "<p>\"Just the place for a Snark!\" the Bellman cried,<br>"
        "As he landed his crew with care;<br>"
        "Supporting each man on the top of the tide<br>"
        "By a finger entwined in his hair.</p>"

        "<P>Just the place for a Snark! I have said it twice:<br>"
        "That alone should encourage the crew.<br>"
        "Just the place for a Snark! I have said it thrice:<br>"
        "What I tell you three times is true.</p>"

        "<p>The crew was complete: it included a Boots-<br>"
        "A maker of Bonnets and Hoods-<br>"
        "A Barrister, brought to arrange their disputes-<br>"
        "And a Broker, to value their goods.</p>"

        "<p>A Billiard-marker, whose skill was immense,<br>"
        "Might perhaps have won more than his share-<br>"
        "But a Banker, engaged at enormous expense,<br>"
        "Had the whole of their cash in his care.</p>"

        "<p>There was also a Beaver, that paced on the deck,<br>"
        "Or would sit making lace in the bow:<br>"
        "And had often (the Bellman said) saved them from wreck,<br>"
        "Though none of the sailors knew how.</p>"

        "<p>There was one who was famed for the number of things<br>"
        "He forgot when he entered the ship:<br>"
        "His umbrella, his watch, all his jewels and rings,<br>"
        "And the clothes he had bought for the trip.</p>"
        "<div id=\"a\">"
        "<p>He had forty-two boxes, all carefully packed,<br>"
        "With his name painted clearly on each:<br>"
        "But, since he omitted to mention the fact,<br>"
        "They were all left behind on the beach.</p>"
        "</div>"

        "<p>The loss of his clothes hardly mattered, because<br>"
        "He had seven coats on when he came,<br>"
        "With three pair of boots-but the worst of it was,<br>"
        "He had wholly forgotten his name.</p>"

        "<p>He would answer to \"Hi!\" or to any loud cry,<br>"
        "Such as \"Fry me!\" or \"Fritter my wig!\"<br>"
        "To \"What-you-may-call-um!\" or \"What-was-his-name!\"<br>"
        "But especially \"Thing-um-a-jig!\"</p>"

        "<p>While, for those who preferred a more forcible word,<br>"
        "He had different names from these:<br>"
        "His intimate friends called him \"Candle-ends,\"<br>"
        "And his enemies \"Toasted-cheese.\"</p>"

        "<p>\"His form is ungainly-his intellect small-\"<br>"
        "(So the Bellman would often remark)<br>"
        "\"But his courage is perfect! And that, after all,<br>"
        "Is the thing that one needs with a Snark.\"</p>"

        "<p>He would joke with hyenas, returning their stare<br>"
        "With an impudent wag of the head:<br>"
        "And he once went a walk, paw-in-paw, with a bear,<br>"
        "\"Just to keep up its spirits,\" he said.</p>"

        "<p>He came as a Baker: but owned, when too late-<br>"
        "And it drove the poor Bellman half-mad-<br>"
        "He could only bake Bride-cake-for which, I may state,<br>"
        "No materials were to be had.</p>"

        "<p>The last of the crew needs especial remark,<br>"
        "Though he looked an incredible dunce:<br>"
        "He had just one idea-but, that one being \"Snark,\"<br>"
        "The good Bellman engaged him at once.</p>"

        "<p>He came as a Butcher: but gravely declared,<br>"
        "When the ship had been sailing a week,<br>"
        "He could only kill Beavers. The Bellman looked scared,<br>"
        "And was almost too frightened to speak:</p>"

        "<p>But at length he explained, in a tremulous tone,<br>"
        "There was only one Beaver on board;<br>"
        "And that was a tame one he had of his own,<br>"
        "Whose death would be deeply deplored.</p>"

        "<div id=\"b\">"
        "<p>The Beaver, who happened to hear the remark,<br>"
        "Protested, with tears in its eyes,<br>"
        "That not even the rapture of hunting the Snark<br>"
        "Could atone for that dismal surprise!</p>"
        "</div>"

        "<p style=\"-mupdf-leading:7pt;\">It strongly advised that the Butcher should be<br>"
        "Conveyed in a separate ship:<br>"
        "But the Bellman declared that would never agree<br>"
        "With the plans he had made for the trip:</p>"

        "<p style=\"-mupdf-leading:11pt;\">Navigation was always a difficult art,<br>"
        "Though with only one ship and one bell:<br>"
        "And he feared he must really decline, for his part,<br>"
        "Undertaking another as well.</p>"

        "<p style=\"-mupdf-leading:15pt;\">The Beaver's best course was, no doubt, to procure<br>"
        "A second-hand dagger-proof coat-<br>"
        "So the Baker advised it-and next, to insure<br>"
        "Its life in some Office of note:</p>"

        "<p style=\"-mupdf-leading:20pt;\">This the Banker suggested, and offered for hire<br>"
        "(On moderate terms), or for sale,<br>"
        "Two excellent Policies, one Against Fire,<br>"
        "And one Against Damage From Hail.</p>"

        "<p style=\"-mupdf-leading:30pt;\">Yet still, ever after that sorrowful day,<br>"
        "Whenever the Butcher was by,<br>"
        "The Beaver kept looking the opposite way,<br>"
        "And appeared unaccountably shy.</p>"
        )

mediabox = fitz.Rect(0, 0, 512, 640)
margin = 10
where = fitz.Rect(
        mediabox.x0 + margin,
        mediabox.y0 + margin,
        mediabox.x1 - margin,
        mediabox.y1 - margin,
        )


class Film:
    def __init__(self, title, director, year, cast):
        self.title = title
        self.director = director
        self.year = year
        self.cast = cast

films = [
        Film(
            "Pulp Fiction",
            "Quentin Tarantino",
            "1994",
            [
                "John Travolta",
                "Samuel L Jackson",
                "Uma Thurman",
                "Bruce Willis",
                "Ving Rhames",
                "Harvey Keitel",
                "Tim Roth",
                "Bridget Fonda",
            ],
            ),
        Film(
            "The Usual Suspects",
            "Bryan Singer",
            "1995",
            [
                "Kevin Spacey",
                "Gabriel Byrne",
                "Chazz Palminteri",
                "Benicio Del Toro",
                "Kevin Pollak",
                "Pete Postlethwaite",
                "Steven Baldwin",
            ],
            ),
        Film(
            "Fight Club",
            "David Fincher",
            "1999",
            [
                "Brad Pitt",
                "Edward Norton",
                "Helena Bonham Carter",
            ],
            ),
        ]


festival_template = (
    "<html><head><title>Why do we have a title? Why not?</title></head>"
    "<body><h1 style=\"text-align:center\">Hook Norton Film Festival</h1>"
    "<ol>"
    "<li id=\"filmtemplate\">"
    "<b id=\"filmtitle\"></b>"
    "<dl>"
    "<dt>Director<dd id=\"director\">"
    "<dt>Release Year<dd id=\"filmyear\">"
    "<dt>Cast<dd id=\"cast\">"
    "</dl>"
    "</li>"
    "<ul>"
    "</body></html"
    )


def test_simple():
    print( 'creating fitz.HtmlStory')
    story = fitz.HtmlStory( snark)
    writer = fitz.DocumentWriter( 'out.pdf', '')
    i = 0
    while 1:
        i += 1
        device = writer.begin_page( mediabox)
        done, filled = story.place( where)
        print( f'i={i} done={done}')
        story.draw( device, None)
        writer.end_page()
        if done:
            break
    writer.close()


def test_dom():
    story = fitz.HtmlStory( user_css="", em=11)
    
    dom = story.document()
    body = dom.body()
    
    body.append_child( dom.create_text_node( 'This is some text.'))
    tmp = dom.create_element( 'b')
    body.append_child( tmp)
    tmp.append_child( dom.create_text_node( 'This is some bold text.'))
    body.append_child( dom.create_text_node( 'This is some normal text.'))
    
    writer = fitz.DocumentWriter( 'out2.pdf', '')
    i = 0
    while 1:
        device = writer.begin_page( mediabox)
        done, filled = story.place( where)
        print( f'i={i} done={done}')
        story.draw( device, None)
        writer.end_page()
        if done:
            break
    writer.close()

def test_combination():
    writer = fitz.DocumentWriter( 'out3.pdf', '')
    story = fitz.HtmlStory( festival_template, '', 11)
    dom = story.document()
    body = dom.body()
    template = body.find( None, 'id', 'filmtemplate')
    for film in films:
        film2 = template.clone()
        # Now fill in some of the template.
        tmp = film2.find( None, 'id', 'filmtitle')
        tmp.append_child( dom.create_text_node( film.title))
        
        tmp = film2.find( None, 'id', 'director')
        tmp.append_child( dom.create_text_node( film.director))
        
        tmp = film2.find( None, 'id', 'filmyear')
        tmp.append_child( dom.create_text_node( film.year))

        tmp = film2.find( None, 'id', 'cast')
        for actor in film.cast:
            tmp.append_child( dom.create_text_node( actor))
            tmp.append_child( dom.create_element( 'br'))
        
        template.parent().append_child( film2)

    # Remove the template.
    template.remove()
    
    i = 0
    while 1:
        device = writer.begin_page( mediabox)
        done, filled = story.place( where)
        print( f'i={i} done={done}')
        story.draw( device, None)
        writer.end_page()
        if done:
            break
    writer.close()

