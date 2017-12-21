import wx
import json
import time

import crawler
import myUtils
import pornDB

SETTING_FILENAME = 'setting.json'
DOWNLOADED_FILENAME = '91downloaded.txt'
SRC_FILENAME_TEMPLATE = '91pornSrc%d.txt'

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
        bakBtn = wx.Button(panel, label='Backup')
        bakBtn.Bind(wx.EVT_BUTTON, self.OnBackup)
        self.bakBtn = bakBtn
        
        hbox.Add(getBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(copyBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(setBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(dbBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(bakBtn, proportion=0)

        tc = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc = tc

        vbox.Add((0, 20))
        vbox.Add(hbox, proportion=0, flag=wx.ALIGN_CENTRE_HORIZONTAL, border=10)
        vbox.Add((0, 20))
        vbox.Add(tc, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(vbox)

        copyBtn.Disable()

        self.SetSize((900, 600))
        self.SetTitle('91porn Crawler')
        self.Center()
        self.Show(True)
    
    def OnGetClick(self, e):
        self.getBtn.Disable()
        self.setBtn.Disable()
        self.bakBtn.Disable()

        statusbar = self.statusbar
        setting = myUtils.read(SETTING_FILENAME)
        duration = setting['DURATION']
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
        self.StatusDisplay('Now time is %s\n' % time.asctime())
        self.StatusDisplay('duration=%d, item_amount=%d, domain=%s, chosen=%d' % (duration, item_amount, domain, chosen))
        self.StatusDisplay('inital_id=%d, page_index=%d, last_page=%d\n' % (initial_id, page_index, last_page))

        if not initial_id:
            self.StatusDisplay('initializing table[%s...]' % table, 'table[%s] initializing' % table)
            pornDB.initialDB(table)
            initial_id += 1
            self.StatusDisplay('initialized table[%s]\n' % table, 'table[%s] initialized\n' % table)
        
        self.StatusDisplay('reading hrefs from table[%s]...' % table, 'hrefs reading...')
        hrefs = pornDB.readAllHrefs(table)
        hrefs_firstread_length = len(hrefs)
        self.StatusDisplay('read hrefs from table[%s], length=%d\n' % (table, hrefs_firstread_length), 'hrefs read')

        all_finished = page_index > last_page
        if hrefs_firstread_length == 0 and all_finished:
            wx.MessageBox('table[%s] all finished!' % table, 'info', wx.OK | wx.ICON_INFORMATION)
            return

        if hrefs_firstread_length < item_amount and not all_finished:
            total = hrefs_firstread_length
            self.StatusDisplay('hrefs is not enough, get hrefs from %s...\n' % domain, 'hrefs getting...')
            crawler_hrefs = []
            
            while total < item_amount and page_index <= last_page:
                self.StatusDisplay('get %s%s begins...' % (domain, path))
                c_hrefs = crawler.getHref(path, domain, page_index , initial_id)
                self.StatusDisplay('got %s%s\n' % (domain, path))
                c_hrefs_length = len(c_hrefs)
                total += c_hrefs_length
                initial_id += c_hrefs_length
                page_index += 1
                crawler_hrefs += c_hrefs
            
            self.StatusDisplay('got hrefs from %s\n' % domain, 'hrefs got')
            self.StatusDisplay('adding hrefs to table[%s]' % table, 'hrefs adding...')
            pornDB.addHrefs(crawler_hrefs, table)
            self.StatusDisplay('added hrefs to table[%s] successfully\n' % table, 'hrefs added')

            serie['itemId'] = initial_id
            serie['pageIndex'] = page_index
            setting['lastModified'] = time.asctime()
            myUtils.write(SETTING_FILENAME, setting, indent=2)
            self.StatusDisplay('in table[%s], itemId updated to %d, pageIndex updated to %d\n' % (table, initial_id, page_index))

            self.StatusDisplay('read hrefs from table[%s] again...' % table, 'hrefs reading again...')
            hrefs = pornDB.readAllHrefs(table)
            hrefs_length = len(hrefs)
            self.StatusDisplay('read hrefs from table[%s], length is %d\n' % (table, hrefs_length), 'hrefs read again')

        hrefs = hrefs[:item_amount]
        hrefs_length = len(hrefs)
        self.StatusDisplay('handle hrefs in table[%s] done, length=%d\n' % (table, hrefs_length))

        self.StatusDisplay('get src in table[%s] begins...\n' % table, 'src getting...')
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

            if duration:
                time.sleep(duration)

        self.StatusDisplay('filter srcs from table[%s] begins...' % table, 'srcs filtering...')
        mp4s = myUtils.read(DOWNLOADED_FILENAME)
        srcs_filtered = []
        mp4s_repeat = []
        mp4s_new = []
        for src in srcs:
            mp4 = myUtils.matchMp4(src)
            is_inserted = myUtils.insertIntoOrdered(mp4, mp4s)
            if is_inserted:
                mp4s_new.append(mp4)
                srcs_filtered.append(src)
            else:
                mp4s_repeat.append(mp4)
                self.StatusDisplay('%d.mp4 has been downloaded before!' % mp4)
                self.StatusDisplay('(src = %s)' % src)
        self.StatusDisplay('filtered srcs from table[%s]\n' % table, 'srcs filtered')

        counter_new = len(mp4s_new)
        counter_repeat = len(mp4s_repeat)
        if counter_repeat:
            self.StatusDisplay('%s repeated\n' % mp4s_repeat)
        else:
            self.StatusDisplay('none mp4 repeated\n')

        self.StatusDisplay('%s to be wrote into %s' %(mp4s_new, DOWNLOADED_FILENAME))
        self.StatusDisplay('write new mp4s into %s...' % DOWNLOADED_FILENAME, 'mp4s writing...')
        myUtils.write(DOWNLOADED_FILENAME, mp4s)
        self.StatusDisplay('write new mp4s into %s successfully!\n' % DOWNLOADED_FILENAME, 'mp4s wrote')

        self.StatusDisplay('%s to be downloaded' % mp4s_new)
        self.StatusDisplay('got %d srcs(total %d, repeated %d) from table[%s]' % (counter_new, counter_get, counter_repeat, table),
            'src got')

        srcTxt = '\n'.join(srcs_filtered)
        myUtils.write(SRC_FILENAME_TEMPLATE % myUtils.getTimeStamp(), srcTxt, file_type='string')
        self.srcTxt = srcTxt
        self.StatusDisplay(srcTxt + '\n')

        if counter_get:
            ids = myUtils.filterIds(hrefs)
            self.StatusDisplay('ids prepared to delete in table[%s] is %s' % (table, ids))
            self.StatusDisplay('delete hrefs from table[%s] begins...' % table, 'hrefs deleting...')
            pornDB.deleteHrefs(ids, table)
            self.StatusDisplay('deleted hrefs from table[%s]\n' % table, 'hrefs deleted')
            self.copyBtn.Enable()
        
        self.StatusDisplay('All done! Enjoy!', 'done')
        self.StatusDisplay('Now time is %s' % time.asctime())
        wx.MessageBox('Enjoy! Got %d srcs(total %d, repeated %d) from table[%s]' % (counter_new, counter_get, counter_repeat, table),
            'info', wx.OK | wx.ICON_INFORMATION)

        self.getBtn.Enable()
        self.setBtn.Enable()
        self.bakBtn.Enable()
    
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
        dial = DatabaseDialog(None, title='Database')
        dial.ShowModal()
        dial.Destroy()
    
    def OnBackup(self, e):
        dial = wx.MessageDialog(None,
            'Are you sure to backup %s and %s, this will cover old backup files' % (SETTING_FILENAME, DOWNLOADED_FILENAME),
            'Warn', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return
        
        self.StatusDisplay('back up %s and %s begins...' % (SETTING_FILENAME, DOWNLOADED_FILENAME), 'backuping...')
        myUtils.backup(SETTING_FILENAME, indent=2)
        myUtils.backup(DOWNLOADED_FILENAME)
        self.StatusDisplay('back up %s and %s successfully!' % (SETTING_FILENAME, DOWNLOADED_FILENAME),
            'backup successfully')
        wx.MessageBox('back up %s and %s successfully!' % (SETTING_FILENAME, DOWNLOADED_FILENAME),
            'info', wx.OK | wx.ICON_INFORMATION)
    
    def StatusDisplay(self, txt, statusTxt=None):
        self.tc.AppendText(txt + '\n')
        if statusTxt:
            self.statusbar.SetStatusText(statusTxt)

class MyDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setting = myUtils.read(SETTING_FILENAME)
        self.serieLabels = [key for key in self.setting['series'][0]]
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

        serieLabels = self.serieLabels
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
        for p in self.serieLabels:
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
        myUtils.write(SETTING_FILENAME, setting, indent=2)
        wx.MessageBox('setting.json saved successfully', 'info', wx.OK | wx.ICON_INFORMATION)

    def OnClose(self, e):
        self.Close()

class DatabaseDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setting = myUtils.read(SETTING_FILENAME)
        self.series = self.setting['series']
        self.selected_serie = self.series[self.setting['chosen']]
        self.table = self.selected_serie['title']
        self.tables = list(map(lambda s: s['title'], self.series))
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer()
        st = wx.StaticText(panel, label='table:')
        cb = wx.ComboBox(panel, value=self.table, choices=self.tables, style=wx.CB_READONLY)
        cb.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        btn = wx.Button(panel, label='Reset')
        btn.Bind(wx.EVT_BUTTON, self.OnReset)
        hbox.Add(st, flag=wx.TOP | wx.RIGHT, border=5)
        hbox.Add(cb, flag=wx.TOP | wx.RIGHT, border=3)
        hbox.Add(btn, flag=wx.LEFT, border=20)
        vbox.Add(hbox, flag=wx.ALL, border=10)

        txt = self.GetTxt()
        tc = wx.TextCtrl(panel, value=txt, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc = tc
        vbox.Add(tc, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        panel.SetSizer(vbox)

        self.SetSize(1000, 500)
        self.Center()
        self.Show(True)
    
    def OnSelect(self, e):
        self.table = e.GetString()
        self.selected_serie = myUtils.find(self.table, self.series, 'title')
        self.tc.SetValue(self.GetTxt())
    
    def OnReset(self, e):
        setting = self.setting
        table = self.table
        selected_serie = self.selected_serie

        dial = wx.MessageDialog(None, 'Are you sure to reset table[%s]' % table, 'Warn',
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return

        if not selected_serie['itemId']:
            wx.MessageBox('table[%s] has not been initialized' % table, 'info', wx.OK | wx.ICON_INFORMATION)
            return
        
        self.tc.SetValue('table=%s, length=0' % self.table)
        pornDB.clearHrefs(table)

        selected_serie['itemId'] = 1
        selected_serie['pageIndex'] = 1
        setting['lastModified'] = time.asctime()
        myUtils.write(SETTING_FILENAME, setting, indent=2)
        wx.MessageBox('table[%s] has been reset!' % table, 'info', wx.OK | wx.ICON_INFORMATION)

    def GetTxt(self):
        table = self.table
        
        if not self.selected_serie['itemId']:
            return 'table[%s] has not initialized' % table

        hrefs = pornDB.readAllHrefs(table)
        hrefs_length = len(hrefs)
        for href in hrefs:
            del href['done']
        txt = myUtils.dictArray2str(hrefs)
        tcTxt = 'table=%s, length=%d\n\n%s' % (table, hrefs_length, txt)
        return tcTxt

if __name__ == '__main__':
    app = wx.App()
    MyFrame(None)
    app.MainLoop()