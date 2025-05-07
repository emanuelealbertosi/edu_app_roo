Option Compare Database
Option Explicit

' Definizioni delle costanti utilizzate nello script
' Tipi di campo per DAO
Const dbBoolean = 1
Const dbByte = 2
Const dbInteger = 3
Const dbLong = 4
Const dbCurrency = 5
Const dbSingle = 6
Const dbDouble = 7
Const dbDate = 8
Const dbText = 10
Const dbLongBinary = 11
Const dbMemo = 12
Const dbGUID = 15

' Costanti per gli attributi della tabella
Const dbAttachedTable = 1024
Const dbAttachedODBC = 2048

' Costanti per le viste del modulo
Const acNormal = 0
Const acDesign = 1
Const acPreview = 2
Const acFormDS = 3
Const acFormPivotTable = 4
Const acFormPivotChart = 5

' Costanti per i tipi di controllo
Const acLabel = 100
Const acTextBox = 109
Const acCommandButton = 104
Const acCheckBox = 106
Const acOptionButton = 105
Const acComboBox = 111
Const acListBox = 110
Const acSubform = 112
Const acImage = 103
Const acLine = 102
Const acRectangle = 101
Const acPage = 124
Const acToggleButton = 122
Const acTabCtl = 123

' Script per estrarre informazioni strutturali da un database Access in formato testuale
' Include tabelle, query, maschere e le loro proprietà

Sub ExportDatabaseStructure()
    Dim db As DAO.Database
    Dim tdf As DAO.TableDef
    Dim qdf As DAO.QueryDef
    Dim fld As DAO.Field
    Dim prp As DAO.Property
    Dim frm As AccessObject
    Dim strPath As String
    Dim intFileNum As Integer
    Dim i As Integer
    
    ' Richiedi percorso file per il salvataggio
    strPath = InputBox("Inserisci il percorso completo dove salvare il file di esportazione:", _
                      "Esportazione struttura database", CurrentProject.Path & "\DB_Structure.txt")
    
    If strPath = "" Then
        MsgBox "Operazione annullata dall'utente.", vbInformation
        Exit Sub
    End If
    
    ' Apri il file di testo per la scrittura
    intFileNum = FreeFile
    Open strPath For Output As intFileNum
    
    Set db = CurrentDb
    
    ' -------------- INTESTAZIONE --------------
    Print #intFileNum, "STRUTTURA DATABASE: " & CurrentProject.Name
    Print #intFileNum, "Data di esportazione: " & Format(Now(), "dd/mm/yyyy hh:mm:ss")
    Print #intFileNum, String(100, "=")
    Print #intFileNum, ""
    
    ' -------------- TABELLE --------------
    Print #intFileNum, "TABELLE"
    Print #intFileNum, String(100, "-")
    
    For Each tdf In db.TableDefs
        ' Esclude le tabelle di sistema
        If Left(tdf.Name, 4) <> "MSys" And Left(tdf.Name, 4) <> "~TMP" Then
            Print #intFileNum, "TABELLA: " & tdf.Name
            Print #intFileNum, "  Descrizione: " & GetTableDescription(tdf.Name)
            Print #intFileNum, "  Tipo: " & GetTableType(tdf)
            Print #intFileNum, ""
            Print #intFileNum, "  CAMPI:"
            
            ' Elenca i campi della tabella
            For Each fld In tdf.Fields
                Print #intFileNum, "    - " & fld.Name & " (" & GetFieldTypeName(fld.Type) & ")"
                Print #intFileNum, "      Dimensione: " & fld.Size
                
                ' Verifica se è chiave primaria
                If IsPrimaryKey(tdf.Name, fld.Name) Then
                    Print #intFileNum, "      Chiave Primaria: Sì"
                End If
                
                ' Elenca le proprietà aggiuntive del campo
                For Each prp In fld.Properties
                    On Error Resume Next
                    If Not (prp.Name = "Name" Or prp.Name = "Type" Or prp.Name = "Size" Or prp.Name = "Required" Or prp.Name = "OrdinalPosition") Then
                        If Err.Number = 0 Then
                            Print #intFileNum, "      " & prp.Name & ": " & prp.Value
                        End If
                    End If
                    On Error GoTo 0
                Next prp
                
                Print #intFileNum, ""
            Next fld
            
            Print #intFileNum, String(80, "-")
        End If
    Next tdf
    
    ' -------------- QUERY --------------
    Print #intFileNum, ""
    Print #intFileNum, "QUERY"
    Print #intFileNum, String(100, "-")
    
    For Each qdf In db.QueryDefs
        Print #intFileNum, "QUERY: " & qdf.Name
        Print #intFileNum, "  Tipo: " & GetQueryType(qdf.Type)
        Print #intFileNum, "  SQL: " & qdf.SQL
        Print #intFileNum, ""
        
        ' Elenca i campi della query
        Print #intFileNum, "  CAMPI RESTITUITI:"
        On Error Resume Next
        For Each fld In qdf.Fields
            Print #intFileNum, "    - " & fld.Name & " (" & GetFieldTypeName(fld.Type) & ")"
        Next fld
        On Error GoTo 0
        
        Print #intFileNum, String(80, "-")
    Next qdf
    
    ' -------------- MASCHERE --------------
    Print #intFileNum, ""
    Print #intFileNum, "MASCHERE"
    Print #intFileNum, String(100, "-")
    
    For Each frm In CurrentProject.AllForms
        Print #intFileNum, "MASCHERA: " & frm.Name
        
        ' Apri la maschera in modalità di progettazione per leggerne le proprietà
        DoCmd.OpenForm frm.Name, acDesign, , , , acHidden
        
        Print #intFileNum, "  Origine record: " & Forms(frm.Name).RecordSource
        Print #intFileNum, "  Caption: " & Forms(frm.Name).Caption
        Print #intFileNum, "  Tipo visualizzazione predefinita: " & GetFormViewType(Forms(frm.Name).DefaultView)
        
        ' Elenca i controlli presenti nella maschera
        ListFormControls intFileNum, frm.Name
        
        ' Chiudi la maschera senza salvare eventuali modifiche
        DoCmd.Close acForm, frm.Name, acSaveNo
        
        Print #intFileNum, String(80, "-")
    Next frm
    
    Close #intFileNum
    
    MsgBox "Esportazione completata con successo!" & vbCrLf & _
           "File salvato in: " & strPath, vbInformation
           
End Sub

' Funzione per determinare il tipo di tabella
Function GetTableType(tdf As DAO.TableDef) As String
    If tdf.Attributes And dbAttachedTable Then
        GetTableType = "Tabella collegata"
    ElseIf tdf.Attributes And dbAttachedODBC Then
        GetTableType = "Tabella ODBC collegata"
    Else
        GetTableType = "Tabella locale"
    End If
End Function

' Funzione per ottenere il nome descrittivo del tipo di campo
Function GetFieldTypeName(intType As Integer) As String
    Select Case intType
        Case dbBoolean: GetFieldTypeName = "Sì/No"
        Case dbByte: GetFieldTypeName = "Byte"
        Case dbInteger: GetFieldTypeName = "Intero"
        Case dbLong: GetFieldTypeName = "Intero lungo"
        Case dbCurrency: GetFieldTypeName = "Valuta"
        Case dbSingle: GetFieldTypeName = "Singolo"
        Case dbDouble: GetFieldTypeName = "Doppio"
        Case dbDate: GetFieldTypeName = "Data/Ora"
        Case dbText: GetFieldTypeName = "Testo"
        Case dbLongBinary: GetFieldTypeName = "Oggetto OLE"
        Case dbMemo: GetFieldTypeName = "Memo"
        Case dbGUID: GetFieldTypeName = "GUID"
        Case Else: GetFieldTypeName = "Tipo sconosciuto (" & intType & ")"
    End Select
End Function

' Funzione per determinare se un campo è chiave primaria
Function IsPrimaryKey(strTable As String, strField As String) As Boolean
    Dim db As DAO.Database
    Dim tdf As DAO.TableDef
    Dim idx As DAO.Index
    Dim fld As DAO.Field
    
    IsPrimaryKey = False
    
    Set db = CurrentDb
    Set tdf = db.TableDefs(strTable)
    
    ' Controlla tutti gli indici della tabella
    For Each idx In tdf.Indexes
        If idx.Primary Then
            ' Controlla se il campo fa parte della chiave primaria
            For Each fld In idx.Fields
                If fld.Name = strField Then
                    IsPrimaryKey = True
                    Exit Function
                End If
            Next fld
        End If
    Next idx
End Function

' Funzione per ottenere il tipo di query
Function GetQueryType(intType As Integer) As String
    ' Definizione delle costanti per i tipi di query
    Const dbQSelect = 0
    Const dbQAction = 240
    Const dbQCrosstab = 16
    Const dbQDelete = 32
    Const dbQUpdate = 48
    Const dbQAppend = 64
    Const dbQMakeTable = 80
    Const dbQDDL = 96
    Const dbQSQLPassThrough = 112
    Const dbQSPTBulk = 113
    Const dbQProcedure = 224
    Const dbQUnion = 128
    
    Select Case intType
        Case dbQSelect: GetQueryType = "Select"
        Case dbQAction: GetQueryType = "Action"
        Case dbQCrosstab: GetQueryType = "Crosstab"
        Case dbQDelete: GetQueryType = "Delete"
        Case dbQUpdate: GetQueryType = "Update"
        Case dbQAppend: GetQueryType = "Append"
        Case dbQMakeTable: GetQueryType = "Make-table"
        Case dbQDDL: GetQueryType = "DDL"
        Case dbQSQLPassThrough: GetQueryType = "SQL Pass-through"
        Case dbQSPTBulk: GetQueryType = "SQL Pass-through Bulk"
        Case dbQProcedure: GetQueryType = "Procedure"
        Case dbQUnion: GetQueryType = "Union"
        Case Else: GetQueryType = "Tipo sconosciuto (" & intType & ")"
    End Select
End Function

' Funzione per ottenere il tipo di visualizzazione predefinito di una maschera
Function GetFormViewType(intViewType As Integer) As String
    Select Case intViewType
        Case acNormal: GetFormViewType = "Maschera"
        Case acDesign: GetFormViewType = "Struttura"
        Case acPreview: GetFormViewType = "Anteprima di stampa"
        Case acFormDS: GetFormViewType = "Foglio dati"
        Case acFormPivotTable: GetFormViewType = "Tabella pivot"
        Case acFormPivotChart: GetFormViewType = "Grafico pivot"
        Case Else: GetFormViewType = "Tipo sconosciuto (" & intViewType & ")"
    End Select
End Function

' Funzione per ottenere la descrizione di una tabella
Function GetTableDescription(strTableName As String) As String
    On Error Resume Next
    GetTableDescription = CurrentDb.TableDefs(strTableName).Properties("Description")
    If Err.Number <> 0 Then GetTableDescription = ""
    On Error GoTo 0
End Function

' Procedura per elencare i controlli di una maschera
Sub ListFormControls(intFileNum As Integer, strFormName As String)
    Dim ctl As Control
    Dim strControlType As String
    
    Print #intFileNum, "  CONTROLLI:"
    
    ' Elenca i controlli della maschera
    For Each ctl In Forms(strFormName).Controls
        Select Case ctl.ControlType
            Case acLabel: strControlType = "Etichetta"
            Case acTextBox: strControlType = "Casella di testo"
            Case acCommandButton: strControlType = "Pulsante di comando"
            Case acCheckBox: strControlType = "Casella di controllo"
            Case acOptionButton: strControlType = "Pulsante opzione"
            Case acComboBox: strControlType = "Casella combinata"
            Case acListBox: strControlType = "Casella di riepilogo"
            Case acSubform: strControlType = "Sottomaschera"
            Case acImage: strControlType = "Immagine"
            Case acLine: strControlType = "Linea"
            Case acRectangle: strControlType = "Rettangolo"
            Case acPage: strControlType = "Pagina"
            Case acToggleButton: strControlType = "Pulsante di attivazione/disattivazione"
            Case acTabCtl: strControlType = "Controllo scheda"
            Case Else: strControlType = "Altro controllo (" & ctl.ControlType & ")"
        End Select
        
        Print #intFileNum, "    - " & ctl.Name & " (" & strControlType & ")"
        
        ' Informazioni specifiche per alcuni tipi di controlli
        Select Case ctl.ControlType
            Case acTextBox
                On Error Resume Next
                Print #intFileNum, "      Origine controllo: " & ctl.ControlSource
                On Error GoTo 0
            Case acSubform
                On Error Resume Next
                Print #intFileNum, "      Origine: " & ctl.SourceObject
                On Error GoTo 0
            Case acComboBox, acListBox
                On Error Resume Next
                Print #intFileNum, "      Origine riga: " & ctl.RowSource
                Print #intFileNum, "      Origine controllo: " & ctl.ControlSource
                On Error GoTo 0
        End Select
    Next ctl
End Sub