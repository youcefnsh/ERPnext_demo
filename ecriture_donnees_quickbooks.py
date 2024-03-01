


#Voici une des méthodes de l'objet QuickBooksSync qui permet d'ecrire les factures sur Quickbooks

class QuickBooksSync:
    def __init__(self, client_id, client_secret, environment, redirect_uri, refresh_token, company_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment = environment
        self.redirect_uri = redirect_uri
        self.refresh_token = refresh_token
        self.company_id = company_id
    

    def sync_sales_invoice(self, transactions, all_accounts, erp_accounts):
        try:
            auth_client = AuthClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                environment=self.environment,
                redirect_uri=self.redirect_uri,
            )
            auth_client.refresh(refresh_token=self.refresh_token)
            client = QuickBooks(
                auth_client=auth_client,
                company_id=self.company_id
            )
        except Exception as e:
            print(f"Erreur lors de l'initialisation du client QuickBooks : {str(e)}")
            return

        all_invoices = Invoice.all(qb=client)

        for transaction in transactions:
            try:


                local_debit_account = next((account for account in erp_accounts if account.erpnext_name == transaction['debit_to']), None)
                if not local_debit_account:
                    print(f"Compte débit local '{transaction['debit_to']}' inexistant.")
                    continue
                debit_account = next((account for account in all_accounts if account.Name == str(local_debit_account.quickbooks_name)), None)
                if not debit_account:
                    print(f"Compte débit '{transaction['debit_to']}' inexistant.")
                    continue



                local_income_account = next((account for account in erp_accounts if account.erpnext_name == transaction['against_income_account']), None)
                if not local_income_account:
                    print(f"Compte de revenu local '{transaction['against_income_account']}' inexistant.")
                    continue
                income_account = next((account for account in all_accounts if account.Name == str(local_income_account.quickbooks_name)), None)
                if not income_account:
                    print(f"Compte de revenu '{transaction['against_income_account']}' inexistant.")
                    continue


                customer_name = transaction['customer']
                customers = Customer.query("SELECT * FROM Customer WHERE DisplayName = '{0}'".format(customer_name), qb=client)
                if not customers:
                    print(f"Aucun client trouvé avec le nom '{customer_name}'.")
                    continue

                customer_ref = Ref()
                customer_ref.value = customers[0].Id
                customer_ref.name = customers[0].DisplayName


                item_ref = Ref()
                items = Item.query("SELECT * FROM Item WHERE Name = '{0}'".format(transaction['name']), qb=client)
                if items:
                    item = items[0]
                    item_ref.value = item.Id
                else:
 
                    item = Item()
                    item.Name = transaction['name']
                    item.Type = 'Service'  

                    item.IncomeAccountRef = Ref()
                    item.IncomeAccountRef.value = income_account.Id
                    item.IncomeAccountRef.name = income_account.Name
                    item.save(qb=client)
                    item_ref.value = item.Id


                existing_invoice = next((invoice for invoice in all_invoices if invoice.DocNumber == transaction['name']), None)
                if existing_invoice:
                    print(f"Facture {transaction['name']} existe déjà.")
                    continue

                invoice = Invoice()
                invoice.DocNumber = transaction['name']  
                invoice.CustomerRef = customer_ref

    
                line = SalesItemLine()
                line.Amount = transaction['base_grand_total']  
                line.DetailType = "SalesItemLineDetail"
                line.SalesItemLineDetail = SalesItemLineDetail()
                line.SalesItemLineDetail.ItemRef = item_ref

                invoice.Line.append(line)


                invoice.save(qb=client)
                print(f"Facture pour la transaction {transaction['base_grand_total']} ajoutée avec succès.")
            except Exception as e:
                print(f"Erreur lors de l'ajout de la facture pour la transaction {transaction['base_grand_total']}: {str(e)}")

        return {
            'transactions': transactions,
            'refresh_token': auth_client.refresh_token
        }