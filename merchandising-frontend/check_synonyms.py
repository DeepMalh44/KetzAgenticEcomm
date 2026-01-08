import os
import sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
key = os.getenv("AZURE_SEARCH_KEY")

if not endpoint or not key:
    print("❌ Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY")
    sys.exit(1)

client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))

print("\n🔍 Checking synonym maps in Azure AI Search...\n")

try:
    # Get synonym maps
    synonym_maps = client.get_synonym_maps()
    
    if not synonym_maps:
        print("⚠️  No synonym maps found")
    else:
        print(f"✅ Found {len(synonym_maps)} synonym map(s):\n")
        for sm in synonym_maps:
            print(f"📋 Name: {sm.name}")
            
            # Handle both string and list formats
            synonyms_text = sm.synonyms if isinstance(sm.synonyms, str) else '\n'.join(sm.synonyms)
            
            if synonyms_text.strip():
                print(f"   Synonyms:")
                for line in synonyms_text.split('\n'):
                    if line.strip():
                        print(f"   • {line.strip()}")
            else:
                print("   ⚠️  No synonyms defined yet")
            print()
            
    # Check if products index uses synonym maps  
    print("\n🔍 Checking 'products' index configuration...\n")
    index = client.get_index("products")
    
    fields_with_synonyms = []
    for field in index.fields:
        if hasattr(field, 'synonym_map_names') and field.synonym_map_names:
            fields_with_synonyms.append((field.name, field.synonym_map_names))
    
    if fields_with_synonyms:
        print("✅ Fields configured to use synonym maps:")
        for field_name, maps in fields_with_synonyms:
            print(f"   • {field_name}: {', '.join(maps)}")
    else:
        print("⚠️  No fields are configured to use synonym maps yet")
        print("\n�� Searchable fields in index:")
        for field in index.fields:
            if field.searchable:
                print(f"   • {field.name} (searchable)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
