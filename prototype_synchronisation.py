#Voici un des premiers prototypes de la vue utilisée pour synchroniser les données 


class SyncDataView(FormView):
    form_class = SyncForm
    template_name = 'syncdata.html'

    def form_valid(self, form):
        erp_login = LoginErp.get_current()
        if not erp_login:
            return redirect('login_erp')

        qb_login = LoginQuickbooks.get_current()
        if not qb_login:
            return redirect('login_quickbooks')

        accounts = Account.objects.filter(url=erp_login.url).exclude(quickbooks_name__isnull=True).exclude(quickbooks_name='')
        total_accounts = accounts.count()


        erp = Erp(erp_url, erp_email, erp_pwd)
        qb_sync = QuickBooksSync(
            qb_login.client_id, 
            qb_login.client_secret, 
            qb_login.environment, 
            qb_login.redirect_uri, 
            qb_login.refresh_token, 
            qb_login.company_id
        )

        get_account_response = qb_sync.get_accounts()
        LoginQuickbooks.update_refresh_token(get_account_response['refresh_token'])
        all_quickbooks_accounts = get_account_response['all_accounts']

        # Synchronisation des comptes si la case est cochée
        if form.cleaned_data['sync_customers']:
            customers = erp.get_customers()
            customer_response = qb_sync.sync_customers(customers)
            LoginQuickbooks.update_refresh_token(customer_response['refresh_token'])

        if form.cleaned_data['sync_suppliers']:
            suppliers = erp.get_suppliers()
            supplier_response=qb_sync.sync_suppliers(suppliers)
            LoginQuickbooks.update_refresh_token(supplier_response['refresh_token'])


        successful_syncs = 0
        failed_syncs = 0

        for account in accounts:
            try:
                account_name = account.erpnext_name

                if form.cleaned_data['sync_sales_invoices']:
                    sales_invoices = erp.get_sales_invoices(account_name)
                    invoice_response = qb_sync.sync_sales_invoice(sales_invoices, all_quickbooks_accounts, accounts)
                    LoginQuickbooks.update_refresh_token(invoice_response['refresh_token'])

                if form.cleaned_data['sync_payment_entries']:
                    payment_entries = erp.get_payment_entries(account_name)
                    payment_response = qb_sync.sync_payment_entries(payment_entries, all_quickbooks_accounts, accounts)
                    LoginQuickbooks.update_refresh_token(payment_response['refresh_token'])

                if form.cleaned_data['sync_purchase_invoices']:
                    purchase_invoices = erp.get_purchase_invoices(account_name)
                    payment_response = qb_sync.sync_purchase_invoice(purchase_invoices, all_quickbooks_accounts, accounts)
                    LoginQuickbooks.update_refresh_token(payment_response['refresh_token'])


                successful_syncs += 1
            except Exception as e:
                print(f"Échec de la synchronisation pour le compte {account.erpnext_name} : {str(e)}")
                failed_syncs += 1

        print(f"{successful_syncs} comptes synchronisés sur {total_accounts}")
        print(f"{failed_syncs} synchronisations échouées sur {total_accounts}")

        return redirect('viewaccounts')