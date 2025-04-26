import random
import pprint


characters = [["Byleth (M)","M"],["Petra","F"],["Ferdinand","M"],["Alois","M"],["Constance","F"],["Linhardt","M"],["Flayn","F"],["Bernadetta","F"],["Ashe","M"],["Felix","M"],["Caspar","M"],["Mercedes","F"],["Leonie", "F"]]

# Unused: "Sword of Begalta","Sword of Moralta","Blutgang","Sword of the Creator","Areadbhar", "Lance of Ruin","Lúin", "Arrow of Indra", "Aymr" "Failnaught", "Tathlum Bow", "Freikugel","Crusher" Vajra-Mushti
# Free anyway: "Training Sword", "Training Lance", "Training Axe", "Training Bow", "Training Gauntlets"
weapons = ["Iron Sword","Steel Sword","Silver Sword","Brave Sword","Killing Edge","Levin Sword","Armorslayer","Rapier","Devil Sword","Wo Dao","Cursed Ashiya Sword","Sword of Zoltan","Thunderbrand","Venin Edge","Mercurius","Iron Lance","Steel Lance","Silver Lance","Brave Lance","Killer Lance","Javelin","Short Spear","Spear","Horseslayer","Blessed Lance","Crescent Sickle","Lance of Zoltan","Spear of Assal","Scythe of Sariel","Venin Lance","Gradivus","Iron Axe","Steel Axe","Silver Axe","Brave Axe","Killer Axe","Bolt Axe","Hand Axe","Short Axe","Tomahawk","Hammer","Devil Axe","Axe of Ukonvasara","Axe of Zoltan","Mace","Venin Axe","Hauteclere","Iron Bow","Steel Bow","Silver Bow","Brave Bow","Killer Bow","Magic Bow","Longbow","Mini Bow","Blessed Bow","The Inexhaustible","Bow of Zoltan","Venin Bow","Parthia","Iron Gauntlets","Steel Gauntlets","Silver Gauntlets","Dragon Claws","Killer Knuckles","Aura Knuckles"]
weapons = weapons + weapons
weapons_per_char = len(weapons) // len(characters) # 13 chars for this list

# Not included: Lord, Pegasus Knight (F)
intermediate_classes = ["Mercenary","Thief","Armored Knight","Cavalier","Brigand","Archer","Mage","Priest", "Dancer"]
intermediate_classes_m = intermediate_classes + ["Brawler (M)","Dark Mage (M)"]
intermediate_classes_f = intermediate_classes

# Not included: Wyvern Rider, Dark Flier (F)
advanced_classes = ["Swordmaster","Assassin","Fortress Knight","Paladin","Warrior","Sniper","Warlock","Bishop","Trickster"]
advanced_classes_m = advanced_classes + ["Hero (M)","Grappler (M)","Dark Bishop (M)","War Monk"]
advanced_classes_b = advanced_classes_m + ["Enlightened One"]
advanced_classes_f = advanced_classes + ["War Cleric","Valkyrie (F)"]

# Not included: Wyvern Lord, Falcon Knight (F)
expert_classes = ["Mortal Savant","Great Knight","Bow Knight","Dark Knight","Holy Knight"]
expert_classes_m = expert_classes + ["War Master (M)"]
expert_classes_f = expert_classes + ["Gremory (F)"]

result_dict = {}

for character in characters:
	if character[1] == "M":
		selected_i = random.sample(intermediate_classes_m, 3)
		if character[0] == "Byleth (M)":
			selected_a = random.sample(advanced_classes_b, 3)
		else:
			selected_a = random.sample(advanced_classes_m, 3)
		selected_e = random.sample(expert_classes_m, 3)
	else:
		selected_i = random.sample(intermediate_classes_f, 3)
		selected_a = random.sample(advanced_classes_f, 3)
		selected_e = random.sample(expert_classes_f, 3)
	selected_w = random.sample(weapons, weapons_per_char)
	for item in selected_w:
		weapons.remove(item)
	selected_w = list(set(selected_w)) # Throw away dupes
	for lst in [selected_w, selected_i, selected_a, selected_e]:
		lst.sort()

	spell_outcome = random.choices(['1', '2', '3', 'all'], weights=[60, 25, 13, 2], k=1)[0]
	result_dict[character[0]] = {
		"Classes": [selected_i, selected_a, selected_e],
		"Weapons": selected_w,
		"Spells": spell_outcome,
	}


print("Character results:")
pprint.pprint(result_dict)
sotc = random.choice(["Yes", "NOOO"])
print(f"Does Byleth have Sword of the Creator access?  The answer is... {sotc}!")
print(f"Leftover unused weapons: {weapons=}")
