import os

# 1. Update LLM.py
llm_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\services\rag\llm.py'
with open(llm_path, 'r', encoding='utf-8') as f:
    llm_code = f.read()

# Replace the dictionary generation part
old_code_block = """            writer = str(row.get('writer', 'Unknown Writer'))
            producer = str(row.get('producer', 'Unknown Producer'))
            studio = str(row.get('studio', 'Unknown Studio'))
            cast = str(row.get('cast', ''))
            awards = str(row.get('awards', 'None'))
            availability = str(row.get('availability', 'Available on Streamora'))
            countries = str(row.get('countries', 'United States'))
            languages = str(row.get('languages', 'English'))
            budget = str(row.get('budget', 'Unknown'))
            revenue = str(row.get('revenue', 'Unknown'))
            box_office = str(row.get('box_office', 'Unknown'))
            franchise = str(row.get('franchise', 'None'))
            trailer_url = str(row.get('trailer_url', ''))"""

new_code_block = """            writer = str(row.get('writer', '')) if pd.notna(row.get('writer')) and row.get('writer') else None
            producer = str(row.get('producer', '')) if pd.notna(row.get('producer')) and row.get('producer') else None
            studio = str(row.get('studio', '')) if pd.notna(row.get('studio')) and row.get('studio') else None
            cast_str = str(row.get('cast', '')) if pd.notna(row.get('cast')) else ''
            awards = str(row.get('awards', '')) if pd.notna(row.get('awards')) and row.get('awards') else None
            availability = str(row.get('availability', '')) if pd.notna(row.get('availability')) and row.get('availability') else None
            countries = str(row.get('countries', '')) if pd.notna(row.get('countries')) and row.get('countries') else None
            languages = str(row.get('languages', '')) if pd.notna(row.get('languages')) and row.get('languages') else None
            budget = str(row.get('budget', '')) if pd.notna(row.get('budget')) and row.get('budget') else None
            revenue = str(row.get('revenue', '')) if pd.notna(row.get('revenue')) and row.get('revenue') else None
            box_office = str(row.get('box_office', '')) if pd.notna(row.get('box_office')) and row.get('box_office') else None
            franchise = str(row.get('franchise', '')) if pd.notna(row.get('franchise')) and row.get('franchise') else None
            trailer_url = str(row.get('trailer_url', '')) if pd.notna(row.get('trailer_url')) and row.get('trailer_url') else None"""

if old_code_block in llm_code:
    llm_code = llm_code.replace(old_code_block, new_code_block)
    
old_cast_block = """"cast": [c.strip() for c in cast.split(",")] if cast else [],"""
new_cast_block = """"cast": list(dict.fromkeys([c.strip() for c in cast_str.split(",") if c.strip()])) if cast_str else [],"""

if old_cast_block in llm_code:
    llm_code = llm_code.replace(old_cast_block, new_cast_block)
    
old_match = """if score > 0:
            match_percentage = int(max(70, 99 - (score * 10)))
        else:
            match_percentage = int(99 - (random.random() * 20))"""

# Stop generating fake 79% Match for TV Series on Movies
new_match = """if score > 0:
            match_percentage = int(max(70, 99 - (score * 10)))
        else:
            match_percentage = None"""
            
if old_match in llm_code:
    llm_code = llm_code.replace(old_match, new_match)
    
# We also need to fix match_percentage to handle None
old_ret = """"match_percentage": match_percentage,"""
new_ret = """"match_percentage": match_percentage,"""

with open(llm_path, 'w', encoding='utf-8') as f:
    f.write(llm_code)
    
# 2. Update app.js
app_path = r'c:\Users\vedan\OneDrive\Attachments\Documents\GitHub\aurora-ai\frontend\app.js'
with open(app_path, 'r', encoding='utf-8') as f:
    app_code = f.read()
    
# Replace the old document.getElementById('modal-director').textContent = ...
old_modal_assignment = """    // Populate metadata grid and bottom details panel
    document.getElementById('modal-director').textContent = m.director || 'Unknown';
    document.getElementById('modal-writers').textContent = m.writer || m.writers || 'Unknown';
    document.getElementById('modal-producers').textContent = m.producer || m.producers || 'Unknown';
    document.getElementById('modal-studios').textContent = m.studio || m.studios || 'Unknown';
    document.getElementById('modal-countries').textContent = m.countries || 'Unknown';
    document.getElementById('modal-languages').textContent = m.languages || 'English';"""

new_modal_assignment = """    // Populate metadata grid and bottom details panel
    function setMetaGrid(id, val) {
        const el = document.getElementById(id);
        if (!el) return;
        if (val && val !== 'Unknown' && val !== 'None') {
            el.textContent = val;
            el.parentElement.style.display = '';
        } else {
            el.parentElement.style.display = 'none';
        }
    }
    
    setMetaGrid('modal-director', m.director);
    setMetaGrid('modal-writers', m.writer || m.writers);
    setMetaGrid('modal-producers', m.producer || m.producers);
    setMetaGrid('modal-studios', m.studio || m.studios);
    setMetaGrid('modal-countries', m.countries);
    setMetaGrid('modal-languages', m.languages || 'English');"""

if old_modal_assignment in app_code:
    app_code = app_code.replace(old_modal_assignment, new_modal_assignment)

# Also fix the TV Series label on movies
old_match_render = """<div class="modal-match-score">${m.match_percentage}% Match TV Series</div>"""
new_match_render = """<div class="modal-match-score">${m.match_percentage ? m.match_percentage + '% Match' : ''} ${m.content_type === 'movie' ? 'Movie' : 'TV Series'}</div>"""

if old_match_render in app_code:
    app_code = app_code.replace(old_match_render, new_match_render)
    
# Fix financial metadata
old_financials = """    document.getElementById('modal-budget').textContent = m.budget || 'Unknown';
    document.getElementById('modal-revenue').textContent = m.revenue || 'Unknown';
    document.getElementById('modal-boxoffice').textContent = m.box_office || 'Unknown';
    document.getElementById('modal-franchise').textContent = m.franchise || 'None';"""
    
new_financials = """    setMetaGrid('modal-budget', m.budget);
    setMetaGrid('modal-revenue', m.revenue);
    setMetaGrid('modal-boxoffice', m.box_office);
    setMetaGrid('modal-franchise', m.franchise);"""

if old_financials in app_code:
    app_code = app_code.replace(old_financials, new_financials)
    
# Rename 'Because You Viewed This'
old_header = """<h3>Because You Viewed This</h3>"""
new_header = """<h3>${m.content_type === 'movie' ? 'Recommended Movies' : 'Recommended Series'}</h3>"""
if old_header in app_code:
    app_code = app_code.replace(old_header, new_header)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Updated llm.py and app.js")
