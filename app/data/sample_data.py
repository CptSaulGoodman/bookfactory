"""Sample data for testing and development."""

from app.models.book import Book, Chapter, Event
from app.models.character import Character, CharacterCollection


def get_sample_book() -> Book:
    """Get sample book data."""
    return Book(
        book_title="Beneath the Iron Skies",
        chapters={
            "1": Chapter(
                title="The Heartbeat of War",
                synopsis="In the cramped quarters of an Allied mess hall during World War II, Samuel 'Sam' Whitaker, a seasoned cook, deftly turns rations into meals that comfort and inspire. Corporal Ethan Clarke finds solace in writing poetry about the camaraderie he observes here, while Private Jimmy O'Reilly embraces Sam's dishes with a childlike enthusiasm. This chapter establishes the mess hall as more than just a place to eat—it's a haven where soldiers find brief respite from the chaos outside.",
                events=[
                    Event(
                        title="The Morning Ritual",
                        description="As dawn breaks over the Allied encampment, Sam Whitaker begins his day at the mess hall with a ritual that grounds him amid the chaos. With practiced precision, he organizes ingredients from the latest supply drop, turning limited resources into something extraordinary. Corporal Ethan Clarke sits quietly in the corner, sketching lines of verse inspired by the symphony of clanging pots and murmured conversations among soldiers seeking comfort before heading out to face another day's uncertainty."
                    ),
                    Event(
                        title="A New Challenge",
                        description="The arrival of a shipment with more rations than expected brings a spark to Sam's eyes as he shares his culinary plans with Lindy Thompson, who manages the supplies. They banter playfully about allocation, their mutual respect for each other's roles evident despite their disagreements. Meanwhile, Private Jimmy O'Reilly eagerly anticipates trying whatever new creation Sam concocts, his enthusiasm infectious among the grumbling troops."
                    ),
                    Event(
                        title="A Quiet Conversation",
                        description="During a lull in activity, Lieutenant Mack Harrison stops by to discuss upcoming strategies with Sam, who offers insights on troop morale. Their conversation reveals mutual respect and understanding of each other's leadership roles—Mack appreciates Sam's ability to lift spirits, while Sam values Mack's strategic mind for maintaining order."
                    )
                ]
            ),
            "2": Chapter(
                title="Echoes of the Past",
                synopsis="Lieutenant Marcus 'Mack' Harrison visits the mess hall, bringing news and seeking Sam's advice on morale-boosting tactics. During their conversation, hints of Sam's mysterious past emerge, drawing Mack's curiosity. Meanwhile, Lindy Thompson manages the supply constraints with an iron fist but finds herself increasingly drawn to Sam's compassionate leadership style."
            ),
            "3": Chapter(
                title="A Recipe for Resilience",
                synopsis="The mess hall faces a severe shortage as new missions deplete supplies. Lindy and Sam clash over resource allocations, yet they must find common ground to keep morale high. This chapter delves into their dynamic—tensions rise but are ultimately resolved through mutual respect and shared goals."
            ),
            "4": Chapter(
                title="Young Hearts in Old Shoes",
                synopsis="Jimmy faces a challenging mission that tests his courage and resolve. Ethan, grappling with the moral complexities of war, offers Jimmy unwavering support. Sam provides guidance and nourishment, both physical and emotional, preparing them for what lies ahead. This chapter highlights themes of growth, bravery, and mentorship within the mess hall's walls."
            ),
            "5": Chapter(
                title="The Fires Still Burn",
                synopsis="As the war reaches a critical point, each character confronts their own personal battles. Sam's past finally comes to light through a poignant revelation that binds him with Mack in unexpected ways. In the end, it's the unity and resilience of this unlikely family—forged over shared meals and stories—that underscores hope amidst despair."
            )
        }
    )


def get_sample_characters() -> CharacterCollection:
    """Get sample character data."""
    return CharacterCollection(chars=[
        Character(
            name="Samuel 'Sam' Whitaker",
            main_character=True,
            role="Cook and Leader",
            summary="A charismatic yet enigmatic figure, Sam is in his late 30s with a rugged exterior that belies his gentle nature. He commands respect among the soldiers not through authority but by understanding their needs. His culinary skills are legendary, turning simple rations into comforting meals that boost morale. Beneath his tough demeanor lies a compassionate soul who deeply cares for the men under his care, often listening to their stories and offering wisdom when needed. Sam's past is shrouded in mystery, hinting at experiences far beyond what he shares."
        ),
        Character(
            name="Corporal Ethan Clarke",
            main_character=True,
            role="Soldier and Observer",
            summary="In his early 20s, Ethan is a thoughtful young man who finds solace in observing the world around him. His keen eyes miss nothing, making him an invaluable asset during missions. At the mess hall, he often sits quietly at the back, writing poetry inspired by the camaraderie and struggles of war. Ethan struggles with his role in the conflict, questioning its purpose and longing for peace. Despite this internal turmoil, he is fiercely loyal to his comrades, ready to stand by them through thick and thin."
        ),
        Character(
            name="Sergeant Linda 'Lindy' Thompson",
            main_character=False,
            role="Supply Officer",
            summary="A no-nonsense woman in her mid-30s, Lindy is the glue that holds the mess hall operations together. Her organizational skills are unmatched, ensuring supplies never run low and everything runs smoothly. Known for her sharp wit and quick temper, she often clashes with Sam over resource allocations but respects his culinary prowess. Beneath her tough exterior lies a deep-seated desire to protect those around her, especially the younger soldiers who remind her of her brother, lost in battle."
        ),
        Character(
            name="Private James 'Jimmy' O'Reilly",
            main_character=False,
            role="Rookie Soldier",
            summary="A young and eager soldier in his early 20s, Jimmy is the quintessential rookie with a heart full of dreams and ideals about serving his country. His naivety often gets him into trouble, but it also brings a much-needed lightness to the group. At the mess hall, he's known for his endless appetite and willingness to try any dish Sam cooks. Despite his inexperience, Jimmy possesses an innate bravery that surprises even himself, growing more confident with each passing day."
        ),
        Character(
            name="Lieutenant Marcus 'Mack' Harrison",
            main_character=False,
            role="Officer and Strategist",
            summary="In his late 30s, Mack is a seasoned officer known for his strategic brilliance and calm under pressure. His presence at the mess hall is rare but impactful, often bringing news of upcoming missions or changes in strategy. With a sharp mind and an even sharper tongue, he navigates the politics of war with ease. However, his dedication to duty sometimes comes at the expense of personal connections, leaving him isolated from those he commands. Despite this, his respect for Sam's leadership style is evident, often seeking advice on maintaining morale among the troops."
        )
    ]) 