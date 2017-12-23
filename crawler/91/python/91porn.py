import wx
import json
import time
from threading import Thread
from wx.lib.pubsub import pub

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

        pub.subscribe(self.updateDisplay, 'update')

    def SendMsg(self, msg1, msg2=None):
        wx.CallAfter(pub.sendMessage, 'update', msg=(msg1, msg2))

    def OnGetClick(self, e):
        t = Thread(target=self.getClick)
        t.start()

    def getClick(self):
        self.getBtn.Disable()
        self.setBtn.Disable()
        self.bakBtn.Disable()

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

        self.SendMsg('script begins...', 'ready')
        self.SendMsg(f'Now time is {time.asctime()}\n')
        self.SendMsg(f'duration={duration}, item_amount={item_amount}, domain={domain}, chosen={chosen}')
        self.SendMsg(f'inital_id={initial_id}, page_index={page_index}, last_page={last_page}\n')

        if not initial_id:
            self.SendMsg(f'initializing table[{table}...]', f'table[{table}] initializing')
            pornDB.initialDB(table)
            initial_id += 1
            self.SendMsg(f'initialized table[{table}]\n', f'table[{table}] initialized\n')
        
        self.SendMsg(f'reading hrefs from table[{table}]...', 'hrefs reading...')
        hrefs = pornDB.readAllHrefs(table)
        hrefs_firstread_length = len(hrefs)
        self.SendMsg(f'read hrefs from table[{table} length={hrefs_firstread_length}\n', 'hrefs read')

        all_finished = page_index > last_page
        if hrefs_firstread_length == 0 and all_finished:
            wx.MessageBox(f'table[{table}] all finished!', 'info', wx.OK | wx.ICON_INFORMATION)
            return

        if hrefs_firstread_length < item_amount and not all_finished:
            total = hrefs_firstread_length
            self.SendMsg(f'hrefs is not enough, get hrefs from {domain}...\n', 'hrefs getting...')
            crawler_hrefs = []
            
            while total < item_amount and page_index <= last_page:
                self.SendMsg(f'get {domain}{path} [page={page_index}] begins...')
                c_hrefs = crawler.getHref(path, domain, page_index , initial_id)
                self.SendMsg(f'got {domain}{path} [page={page_index}]\n')
                c_hrefs_length = len(c_hrefs)
                total += c_hrefs_length
                initial_id += c_hrefs_length
                page_index += 1
                crawler_hrefs += c_hrefs

                if duration:
                    time.sleep(duration)
            
            self.SendMsg(f'got hrefs from {domain}\n', 'hrefs got')
            self.SendMsg(f'adding hrefs to table[{table}]', 'hrefs adding...')
            pornDB.addHrefs(crawler_hrefs, table)
            self.SendMsg(f'added hrefs to table[{table}] successfully\n', 'hrefs added')

            serie['itemId'] = initial_id
            serie['pageIndex'] = page_index
            setting['lastModified'] = time.asctime()
            myUtils.write(SETTING_FILENAME, setting, indent=2)
            self.SendMsg(f'in table[{table}], itemId updated to {initial_id}, pageIndex updated to {page_index}\n')

            self.SendMsg(f'read hrefs from table[{table}] again...', 'hrefs reading again...')
            hrefs = pornDB.readAllHrefs(table)
            hrefs_length = len(hrefs)
            self.SendMsg(f'read hrefs from table[{table}], length is {hrefs_length}\n', 'hrefs read again')

        hrefs = hrefs[:item_amount]
        hrefs_length = len(hrefs)
        self.SendMsg(f'handle hrefs in table[{table}] done, length={hrefs_length}\n')

        self.SendMsg(f'get src in table[{table}] begins...\n', 'src getting...')
        counter = 0
        counter_get = 0
        srcs = []
        for href in hrefs:
            counter += 1
            url = domain + href['href']
            self.SendMsg(f'id={href["id"]}, itemIndex={href["itemIndex"]}, pageIndex={href["pageIndex"]}, counter={counter}')
            self.SendMsg(f'get {url} begins...')
            src = crawler.getSrc(url, self.error_callback)

            if src:
                counter_get += 1
                href['done'] = True
                srcs.append(src)
            self.SendMsg(f'got {url}')
            self.SendMsg(f'{src}\n')

            if duration:
                time.sleep(duration)
        
        box_msg = 'Sorry! Got nothing!'
        if counter_get:
            self.SendMsg(f'filter srcs from table[{table}] begins...', 'srcs filtering...')
            mp4s = myUtils.read(DOWNLOADED_FILENAME)
            self.SendMsg(f'mp4s has been loaded from {DOWNLOADED_FILENAME}, mp4s.length={len(mp4s)}')
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
                    self.SendMsg(f'{mp4}.mp4 has been downloaded before!')
                    self.SendMsg(f'(src = {src})')
            self.SendMsg(f'filtered srcs from table[{table}]\n', 'srcs filtered')

            counter_new = len(mp4s_new)
            counter_repeat = len(mp4s_repeat)

            if counter_repeat:
                self.SendMsg(f'{mp4s_repeat} repeated\n')
            else:
                self.SendMsg('none mp4 repeated\n')

            if counter_new:
                self.SendMsg(f'{mp4s_new} to be wrote into {DOWNLOADED_FILENAME}')
                self.SendMsg(f'write new mp4s into {DOWNLOADED_FILENAME}...', 'mp4s writing...')
                myUtils.write(DOWNLOADED_FILENAME, mp4s)
                self.SendMsg(f'write new mp4s into {DOWNLOADED_FILENAME} successfully!', 'mp4s wrote')
                self.SendMsg(f'now mp4s.length={len(mp4s)}\n')

                self.SendMsg(f'{mp4s_new} to be downloaded')
                self.SendMsg(f'got {counter_new} srcs(total {counter_get}, repeated {counter_repeat}) from table[{table}]',
                    'src got')
                box_msg = f'Enjoy! Got {counter_new} srcs(total {counter_get}, repeated {counter_repeat}) from table[{table}]'

                srcTxt = '\n'.join(srcs_filtered)
                myUtils.write(SRC_FILENAME_TEMPLATE % myUtils.getTimeStamp(), srcTxt, file_type='string')
                self.srcTxt = srcTxt
                self.SendMsg(f'{srcTxt}\n')

                self.copyBtn.Enable()
            else:
                self.SendMsg('got no new mp4s\n')
                self.SendMsg('nothing to be downloaded')

            ids = myUtils.filterIds(hrefs)
            self.SendMsg(f'{ids} prepared to delete in table[{table}]')
            self.SendMsg(f'delete hrefs from table[{table}] begins...', 'hrefs deleting...')
            pornDB.deleteHrefs(ids, table)
            self.SendMsg(f'deleted hrefs from table[{table}]\n', 'hrefs deleted')

            self.SendMsg('All done! Enjoy!', 'done')
        else:
            self.SendMsg('So sad! None src got!\n', 'done')
        
        self.SendMsg(f'Now time is {time.asctime()}')
        wx.MessageBox(box_msg, 'info', wx.OK | wx.ICON_INFORMATION)

        self.getBtn.Enable()
        self.setBtn.Enable()
        self.bakBtn.Enable()
    
    def error_callback(self, e):
        self.StatusDisplay(f'%s{e}')
    
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
            f'Are you sure to backup {SETTING_FILENAME} and {DOWNLOADED_FILENAME}, this will cover old backup files',
            'Warning', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return
        
        self.StatusDisplay(f'back up {SETTING_FILENAME} and {DOWNLOADED_FILENAME} begins...', 'backuping...')
        myUtils.backup(SETTING_FILENAME, indent=2)
        myUtils.backup(DOWNLOADED_FILENAME)
        self.StatusDisplay(f'back up {SETTING_FILENAME} and {DOWNLOADED_FILENAME} successfully!', 'backup successfully')
        wx.MessageBox(f'back up {SETTING_FILENAME} and {DOWNLOADED_FILENAME} successfully!', 'info',
            wx.OK | wx.ICON_INFORMATION)
    
    def updateDisplay(self, msg):
        self.StatusDisplay(*msg)

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

        self.SetSize(515, 480)
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

        dial = wx.MessageDialog(None, f'Are you sure to reset table[{table}]', 'Warning',
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return

        if not selected_serie['itemId']:
            wx.MessageBox(f'table[{table}] has not been initialized', 'info', wx.OK | wx.ICON_INFORMATION)
            return
        
        self.tc.SetValue(f'table={table}, length=0')
        pornDB.clearHrefs(table)

        selected_serie['itemId'] = 1
        selected_serie['pageIndex'] = 1
        setting['lastModified'] = time.asctime()
        myUtils.write(SETTING_FILENAME, setting, indent=2)
        wx.MessageBox(f'table[{table}] has been reset!', 'info', wx.OK | wx.ICON_INFORMATION)

    def GetTxt(self):
        table = self.table
        
        if not self.selected_serie['itemId']:
            return f'table[{table}] has not initialized'

        hrefs = pornDB.readAllHrefs(table)
        hrefs_length = len(hrefs)
        for href in hrefs:
            del href['done']
        txt = myUtils.dictArray2str(hrefs)
        return f'table={table}, length={hrefs_length}\n\n{txt}'

if __name__ == '__main__':
    app = wx.App()
    MyFrame(None)
    app.MainLoop()