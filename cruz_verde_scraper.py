#!/usr/bin/env python3
"""
CRUZ VERDE MEDICATION SCRAPER
PriceSage - Automated Price Comparison Tool
"""

import requests
import json
from datetime import datetime

class CruzVerdeScraper:
    
    def __init__(self):
        self.base_url = "https://api.cruzverde.com.co/product-service/products/product-summary?ids[]="
        self.url_complement = (
            "&fields=name&fields=images&fields=bioequivalence&fields=expressDelivery&fields=isBioequivalent"
            "&fields=stock&fields=categoryId&fields=prices&fields=description&fields=brand&fields=homeDelivery"
            "&fields=storePickup&fields=promotions&fields=prescriptionModel&fields=showModalContraceptive&fields=skipPrescription"
            "&fields=regulated&fields=prescription&fields=minOrderQuantity&fields=isFreezerRequired&fields=extnIsPreSalesEnabled"
            "&fields=pum&fields=listRegionsForSubscription&fields=healthNeeds&fields=pageURL&inventoryId=COCV_zona14"
        )
        
        self.cookies = {
            '_ga': 'GA1.3.1227315593.1716260103',
            '_hjSessionUser_2133166': 'eyJpZCI6IjJmZDc2NDY3LTRjN2YtNTdmNC1hMzhlLTRjMWYxMzU3OGJhOSIsImNyZWF0ZWQiOjE3MTYyNjAxMDYwNDEsImV4aXN0aW5nIjp0cnVlfQ==',
            'mx_customer_id': 'bcxugVwrEXkbaRkrA1kGYYkXcZ',
            'mx_customer_no': '05659449',
            '_hjMinimizedPolls': '1035398%2C1035400%2C1536013%2C1422488',
            'SL_C_23361dd035530_SID': '{"a036dbbb448879f374f2260abb7baf91314ff637":{"sessionId":"NwSGid6p-tDZ6nII24bdo","visitorId":"Y46hUcIpfQFvDyg6-cavU"}}',
            '_tt_enable_cookie': '1',
            '_ttp': '01JS2A815T3N10X6SZ7WGYBJTF_.tt.2',
            '_ga': 'GA1.1.1227315593.1716260103',
            '_gac_UA-149398373-1': '1.1755286015.CjwKCAjwtfvEBhAmEiwA-DsKjvDcEHpH0tM_YY1mJ-J_-GRhCNfa_K5zrNcMA66ks5Lc2O8UVNBSiBoCoI8QAvD_BwE',
            '_gcl_aw': 'GCL.1755286015.CjwKCAjwtfvEBhAmEiwA-DsKjvDcEHpH0tM_YY1mJ-J_-GRhCNfa_K5zrNcMA66ks5Lc2O8UVNBSiBoCoI8QAvD_BwE',
            '_gcl_gs': '2.1.k1$i1755286002$u38120561',
            '_gcl_au': '1.1.53231465.1756126752',
            '_fbp': 'fb.1.1756126752349.5409159153',
            '_gid': 'GA1.3.700626451.1757512066',
            'connect.sid': 's%3Acolombia-eeca2eff-0b66-4ae1-8ffe-e7fbd76d7ebd.x8pQLKXhyB1Cwg97radEe6gcldyUEl%2FcsdflMjn8s%2BQ',
            '_gat': '1',
            '_hjSession_2133166': 'eyJpZCI6IjMwYjNlNThkLTBmMmEtNDg5My05ZWIyLTZiNGNlZjUzNTNjMSIsImMiOjE3NTc1Mjc5OTMyMzUsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==',
            '_ga_CVCO': 'GS2.1.s1757527994$o299$g0$t1757527994$j60$l0$h1636433838',
            'ttcsid': '1757527995453::WFa-Xi-AlDST2JQbKMld.96.1757527995453',
            'ttcsid_CVS2E3JC77U29KB3Q6RG': '1757527995452::fTnzGzVUySWDq7PUbcO9.96.1757527995670',
            '_ga_8P5QMH4CZ5': 'GS2.1.s1757527994$o299$g0$t1757528000$j54$l1$h1105876500',
        }
        
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'es-ES,es;q=0.9',
            'dnt': '1',
            'origin': 'https://www.cruzverde.com.co',
            'priority': 'u=1, i',
            'referer': 'https://www.cruzverde.com.co/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }
        
        # Product SKUs to scrape
        self.products = {
            'finasteride': [
                {'sku': 'COCV_55507', 'name': 'Finapel (Pharmadem)', 'brand': 'Pharmadem'},
                {'sku': 'COCV_95278', 'name': 'Finasterida (Lafrancol)', 'brand': 'Lafrancol'}
            ],
            'levothyroxine': [
                {'sku': 'COCV_20685', 'name': 'Tiroxin 50 mcg x 50 (Siegfried)', 'brand': 'Siegfried'},
                {'sku': 'COCV_391058', 'name': 'Synthorid 50 mcg x 90 (Synthroid)', 'brand': 'Synthroid'}
            ]
        }

    def scrape_product(self, sku):
        """Scrape individual product data"""
        try:
            response = requests.get(
                url=f"{self.base_url}{sku}{self.url_complement}",
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = json.loads(response.text)
            
            if sku not in data:
                return None
                
            product_data = data[sku]
            
            # Extract pricing information
            price_container = product_data.get('prices', {})
            full_price = price_container.get('price-list-col', 0)
            disc_price = float(price_container.get('price-club-col') or price_container.get('price-sale-col') or full_price)
            
            # Calculate percentage off
            percent_off = int((disc_price / full_price) * 100) if full_price > 0 else 0
            
            return {
                'name': product_data.get('name', 'N/A'),
                'brand': product_data.get('brand', 'N/A'),
                'full_price': full_price,
                'discounted_price': disc_price,
                'percent_off': percent_off,
                'price_per_unit': product_data.get('pum', 'N/A'),
                'stock': product_data.get('stock', 0)
            }
            
        except Exception as e:
            print(f"Error scraping product {sku}: {e}")
            return None

    def format_price(self, price):
        """Format price with commas"""
        return f"${price:,.0f}"

    def generate_comparison_table(self, products_data, category):
        """Generate horizontal comparison table for a category"""
        if not products_data:
            return ""
            
        # Calculate column widths based on content
        max_name_len = max(len(p['name']) for p in products_data if p)
        max_brand_len = max(len(p['brand']) for p in products_data if p)
        
        # Create table header
        table = f"\n### {category.upper()} COMPARISON\n\n"
        
        # Header row
        header = f"| {'Product':<{max_name_len}} | {'Brand':<{max_brand_len}} | Full Price | Discounted Price | % Off| Price per Unit       | Stock |\n"
        separator = f"|{'-' * (max_name_len + 2)}|{'-' * (max_brand_len + 2)}|------------|------------------|------|----------------------|-------|\n"
        
        table += header + separator
        
        # Data rows
        for product in products_data:
            if product:
                row = f"| {product['name']:<{max_name_len}} | {product['brand']:<{max_brand_len}} | {self.format_price(product['full_price']):>10} | {self.format_price(product['discounted_price']):>16} | {product['percent_off']:>3}% | {product['price_per_unit']:>14} | {product['stock']:>5} |\n"
                table += row
        
        return table

    def scrape_all_products(self):
        """Scrape all products and generate formatted output"""
        print("Starting Cruz Verde medication scraping...")
        
        all_data = {}
        
        # Scrape each category
        for category, products in self.products.items():
            print(f"Scraping {category} products...")
            category_data = []
            
            for product_info in products:
                print(f"  - Scraping {product_info['name']}...")
                data = self.scrape_product(product_info['sku'])
                if data:
                    category_data.append(data)
                else:
                    print(f"    ❌ Failed to scrape {product_info['name']}")
            
            all_data[category] = category_data
        
        return all_data

    def save_formatted_output(self, all_data, filename="formatted_comparison.md"):
        """Save formatted comparison table to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# CRUZ VERDE MEDICATION COMPARISON TABLE\n")
            f.write("## PriceSage - Horizontal View for Easy Comparison\n")
            f.write(f"*Generated on: {timestamp}*\n")
            
            # Generate tables for each category
            for category, products_data in all_data.items():
                if products_data:
                    table = self.generate_comparison_table(products_data, category)
                    f.write(table)
            
            f.write("\n---\n\n")
        
        print(f"✅ Formatted comparison saved to {filename}")

    def run(self):
        """Main execution method"""
        try:
            # Scrape all products
            all_data = self.scrape_all_products()
            
            # Generate and save formatted output
            self.save_formatted_output(all_data)
            
            print("\n🎉 Data Successfully Collected and Formatted!")
            print("📊 Check 'formatted_comparison.md' for the horizontal comparison table")
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")

def main():
    """Main function"""
    scraper = CruzVerdeScraper()
    scraper.run()

if __name__ == "__main__":
    main()
