#Voici une des méthodes de la classe Erp qui permet de récupérer les données erp 


class Erp:
    def __init__(self, url, email, password):
        self.client = FrappeClient(url, email, password)

    def get_sales_invoices(self, account_name):
            def correct_unicode_escapes(s):
                return s.encode('latin1').decode('unicode_escape')

            # Obtention de toutes les factures de vente où "debit_to" ou "against_income_account" est égal à account_name
            debit_to_invoices = self.client.get_list("Sales Invoice", fields=["*"], filters={"debit_to": account_name}, limit_page_length=10000)
            against_income_account_invoices = self.client.get_list("Sales Invoice", fields=["*"], filters={"against_income_account": account_name}, limit_page_length=10000)
            
            # Combinaison des factures
            invoices = debit_to_invoices + against_income_account_invoices

            # Parcourir chaque facture pour obtenir des informations supplémentaires
            for invoice in invoices:
                # Correct unicode escapes in account names
                invoice['debit_to'] = correct_unicode_escapes(invoice['debit_to'])
                invoice['against_income_account'] = correct_unicode_escapes(invoice['against_income_account'])
                

                # Obtention des détails du client
                customer = self.client.get_doc("Customer", invoice.get("customer"))
                invoice["customer_details"] = customer

                # Obtention des détails des articles facturés
                items = []
                for item in invoice.get("items", []):
                    item_doc = self.client.get_doc("Item", item.get("item_code"))
                    item["item_details"] = item_doc
                    items.append(item)
                invoice["items"] = items

            return invoices



