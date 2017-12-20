import wx
import json
import time

import crawler
import myUtils
import pornDB

SETTING_FILENAME = 'setting.json'
ITEM_AMOUNT_PERPAGE = 20

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)

        self.statusbar = self.CreateStatusBar()

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer()

        getBtn = wx.Button(panel, label='Get')
        self.getBtn = getBtn
        getBtn.Bind(wx.EVT_BUTTON, self.OnGetClick)
        copyBtn = wx.Button(panel, label='Copy')
        copyBtn.Bind(wx.EVT_BUTTON, self.OnCopy)
        self.copyBtn = copyBtn
        setBtn = wx.Button(panel, label='Setting')
        self.setBtn = setBtn
        setBtn.Bind(wx.EVT_BUTTON, self.OnSet)
        dbBtn = wx.Button(panel, label='Database')
        dbBtn.Bind(wx.EVT_BUTTON, self.OnDB)
        self.dbBtn = dbBtn
        
        hbox.Add(getBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(copyBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(setBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(dbBtn, proportion=0)

        tc = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc = tc

        vbox.Add((0, 20))
        vbox.Add(hbox, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=10)
        vbox.Add((0, 20))
        vbox.Add(tc, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(vbox)

        self.SetSize((900, 600))
        self.SetTitle('91porn Crawler')
        self.Center()
        self.Show(True)
    
    def OnGetClick(self, e):
        self.getBtn.Disable()
        self.setBtn.Disable()
        self.copyBtn.Disable()

        setting = myUtils.read(SETTING_FILENAME)
        statusbar = self.statusbar
        item_amount = setting['ITEM_AMOUNT']
        domain = setting['domain']
        chosen = setting['chosen']

        serie = setting['series'][chosen]
        table = serie['title']
        initial_id = serie['itemId']
        page_index = serie['pageIndex']
        last_page = serie['lastPage']
        path = serie['path']

        self.StatusDisplay('script begins...', 'ready')
        self.StatusDisplay('item_amount=%d, domain=%s, chosen=%d' % (item_amount, domain, chosen))
        self.StatusDisplay('inital_id=%d, page_index=%d, last_page=%d\n' % (initial_id, page_index, last_page))

        if not initial_id:
            self.StatusDisplay('initializing %s...' % table, '%s initializing' % table)
            pornDB.initialDB(table)
            initial_id += 1
            self.StatusDisplay('initialized %s' % table, '%s initialized\n' % table)
        
        self.StatusDisplay('reading hrefs from %s...' % table, 'hrefs reading...')
        hrefs = pornDB.readAllHrefs(table)
        hrefs_length = len(hrefs)
        self.StatusDisplay('read hrefs from %s, length=%d\n' % (table, hrefs_length), 'hrefs read')

        all_finished = page_index > last_page
        if hrefs_length == 0 and all_finished:
            wx.MessageBox('%s all finished!' % table, 'info', wx.OK | wx.ICON_INFORMATION)
            return

        if hrefs_length < item_amount and not all_finished:
            self.StatusDisplay('hrefs is not enough, get hrefs from net...\n', 'hrefs getting...')
            n = (item_amount - hrefs_length) // ITEM_AMOUNT_PERPAGE + 1
            crawler_hrefs = []
            
            for i in range(n):
                self.StatusDisplay('get %s%s begins...' % (domain, path))
                c_hrefs = crawler.getHref(path, domain, page_index , initial_id)
                self.StatusDisplay('got %s%s\n' % (domain, path))
                initial_id += len(c_hrefs)
                page_index += 1
                crawler_hrefs += c_hrefs
                if page_index > last_page:
                    self.StatusDisplay('have met the end of %s\n' % table)
                    break
            
            self.StatusDisplay('got hrefs from net', 'hrefs got')
            self.StatusDisplay('adding hrefs to %s' % table, 'hrefs adding...')
            pornDB.addHrefs(crawler_hrefs, table)
            self.StatusDisplay('added hrefs to %s successfully\n', 'hrefs added')

            serie['itemId'] = initial_id
            serie['pageIndex'] = page_index
            setting['lastModified'] = time.asctime()
            myUtils.write(SETTING_FILENAME, setting)
            self.StatusDisplay('in %s, itemId updated to %d, pageIndex updated to %d\n' % (table, initial_id, page_index))

            self.StatusDisplay('read hrefs from %s again...' % table, 'hrefs reading again...')
            hrefs = pornDB.readAllHrefs(table)
            self.StatusDisplay('read hrefs from %s, length is %d\n' % (table, hrefs_length), 'hrefs read again')

        hrefs = hrefs[:item_amount]
        hrefs_length = len(hrefs)
        self.StatusDisplay('handle hrefs done, length=%d\n' % hrefs_length)

        self.StatusDisplay('get src begins...\n', 'src getting...')
        counter = 0
        counter_get = 0
        srcs = []
        for href in hrefs:
            counter += 1
            url = domain + href['href']
            self.StatusDisplay('id=%d, itemIndex=%d, pageIndex=%d, counter=%d' % (href['id'], href['itemIndex'], href['pageIndex'], counter))
            self.StatusDisplay('get %s begins...' % url)
            src = crawler.getSrc(url, self.error_callback)
            if src:
                counter_get += 1
                href['done'] = True
                srcs.append(src)
            self.StatusDisplay('got %s' % url)
            self.StatusDisplay('%s\n' % src)
        self.StatusDisplay('get %d srcs' % counter_get, 'src got')
        srcTxt = '\n'.join(srcs)
        self.srcTxt = srcTxt

        self.StatusDisplay(srcTxt + '\n')

        if counter_get:
            ids = myUtils.filterIds(hrefs)
            self.StatusDisplay('ids prepared to delete is %s' % ids)
            self.StatusDisplay('delete hrefs begins...', 'hrefs deleting...')
            pornDB.deleteHrefs(ids, table)
            self.StatusDisplay('deleted hrefs\n', 'hrefs deleted')
            self.copyBtn.Enable()
        
        self.StatusDisplay('All done!', 'done')
        wx.MessageBox('Done! Got %d srcs!' % counter_get, 'info', wx.OK | wx.ICON_INFORMATION)

        self.getBtn.Enable()
        self.setBtn.Enable()
    
    def error_callback(self, e):
        self.StatusDisplay('%s' % e)
    
    def OnCopy(self, e):
        data = wx.TextDataObject()
        data.SetText(self.srcTxt)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
            self.statusbar.SetStatusText('src text copied to clipboard')
        else:
            wx.MessageBox('Unable to open the clipboard', 'Error', wx.OK | wx.ICON_ERROR)
    
    def OnSet(self, e):
        dial = MyDialog(None, title='Setting')
        dial.ShowModal()
        dial.Destroy()
    
    def OnDB(self, e):
        setting = myUtils.read(SETTING_FILENAME)
        table = setting['series'][setting['chosen']]['title']
        dial = DatabaseDialog(table, None, title='Database')
        dial.ShowModal()
        dial.Destroy()
    
    def StatusDisplay(self, txt, statusTxt=None):
        self.tc.AppendText(txt + '\n')
        if statusTxt:
            self.statusbar.SetStatusText(statusTxt)

class MyDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setting = myUtils.read(SETTING_FILENAME)
        self.setting_widgets = {}
        self.InitUI()
    
    def InitUI(self):
        setting = self.setting
        CHOICES = [x['title'] for x in self.setting['series']]
        serie = setting['series'][setting['chosen']]
        self.selected_serie_index = serie['index']
        setting_widgets = self.setting_widgets

        panel = wx.Panel(self)
        grid = wx.GridBagSizer(10, 10)

        st1 = wx.StaticText(panel, label='ITEM_AMOUNT')
        grid.Add(st1, pos=(1, 0), flag=wx.LEFT | wx.TOP, border=5)
        sc1 = wx.SpinCtrl(panel, value=str(setting['ITEM_AMOUNT']))
        setting_widgets['item_amount'] = sc1
        grid.Add(sc1, pos=(1, 1))
        st2 = wx.StaticText(panel, label='DURATION')
        grid.Add(st2, pos=(1, 2), flag=wx.LEFT | wx.TOP, border=5)
        sc2 = wx.SpinCtrl(panel, value=str(setting['DURATION']))
        setting_widgets['duration'] = sc2
        grid.Add(sc2, pos=(1, 3))

        st4 = wx.StaticText(panel, label='Domain')
        grid.Add(st4, pos=(2, 0), flag=wx.LEFT | wx.TOP, border=5)
        tc1 = wx.TextCtrl(panel, value=setting['domain'])
        setting_widgets['domain'] = tc1
        grid.Add(tc1, pos=(2, 1), span=(1, 3), flag=wx.EXPAND)

        st5 = wx.StaticText(panel, label='Chosen')
        grid.Add(st5, pos=(3, 0), flag=wx.LEFT | wx.TOP, border=5)
        cb = wx.ComboBox(panel, value=serie['title'], choices=CHOICES, style=wx.CB_READONLY)
        cb.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        grid.Add(cb, pos=(3, 1))

        sbox = wx.StaticBox(panel, label='ChosenSeries')
        ssizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)

        serieLabels = ['index', 'title', 'itemId', 'pageIndex', 'lastPage', 'path']
        serieLabels_length = len(serieLabels)
        for serieLabel in serieLabels:
            hbox = wx.BoxSizer()
            sst1 = wx.StaticText(panel, label=serieLabel + ':')
            sst2 = wx.StaticText(panel, label=str(serie[serieLabel]))
            setting_widgets[serieLabel] = sst2
            hbox.Add(sst1, flag=wx.LEFT, border=15)
            hbox.Add(sst2, flag=wx.LEFT, border=10)
            ssizer.Add(hbox)

        grid.Add(ssizer, pos=(5, 0), span=(serieLabels_length, 4), flag=wx.EXPAND | wx.LEFT, border=10)

        sBtn = wx.Button(panel, label='Save', id=wx.ID_SAVE)
        sBtn.Bind(wx.EVT_BUTTON, self.OnSave)
        cBtn = wx.Button(panel, label='Close', id=wx.ID_CLOSE)
        cBtn.Bind(wx.EVT_BUTTON, self.OnClose)
        btn_pos = serieLabels_length + 6
        grid.Add(sBtn, pos=(btn_pos, 1), flag=wx.ALIGN_CENTER)
        grid.Add(cBtn, pos=(btn_pos, 2), flag=wx.ALIGN_CENTER)

        panel.SetSizer(grid)

        self.SetSize(505, 480)
        self.Center()
        self.Show(True)
    
    def OnSelect(self, e):
        setting = self.setting
        setting_widgets = self.setting_widgets
        serie = myUtils.find(e.GetString(), setting['series'], 'title')
        self.selected_serie_index = serie['index']
        for p in ['index', 'title', 'pageIndex', 'lastPage', 'path']:
            setting_widgets[p].SetLabel(str(serie[p]))
    
    def OnSave(self, e):
        setting = self.setting
        setting_widgets = self.setting_widgets
        setting['chosen'] = self.selected_serie_index

        for w in ['item_amount', 'duration', 'domain']:
            if w == 'domain':
                domain = myUtils.handleDomain(setting_widgets[w].GetValue())
                setting[w] = domain
                setting_widgets[w].SetValue(domain)
            else:
                setting[w.upper()] = int(setting_widgets[w].GetValue())
        setting['lastModified'] = time.asctime()
        myUtils.write(SETTING_FILENAME, setting)
        wx.MessageBox('setting.json saved successfully', 'info', wx.OK | wx.ICON_INFORMATION)

    def OnClose(self, e):
        self.Close()

class DatabaseDialog(wx.Dialog):
    def __init__(self, table, *args, **kw):
        super().__init__(*args, **kw)
        self.table = table
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)
        table = self.table
        hrefs = pornDB.readAllHrefs(table)
        hrefs_length = len(hrefs)
        for href in hrefs:
            del href['done']
        txt = myUtils.dictArray2str(hrefs)
        txt = 'table=%s, length=%d\n\n%s' % (table, hrefs_length, txt)
        tc = wx.TextCtrl(panel, value=txt, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(tc, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        panel.SetSizer(sizer)

        self.SetSize(1000, 500)
        self.Center()
        self.Show(True)

if __name__ == '__main__':
    app = wx.App()
    MyFrame(None)
    app.MainLoop()