// Builds the production files in Adobe Illustrator from artwork/label_print.svg
//   -> print/DKT_Hidden-Fastener-Label_7x5in_PRINT.pdf  (PDF/X-4, CMYK, 0.125in bleed, trim marks, CutContour die line)
//   -> source/DKT_Hidden-Fastener-Label_7x5in.ai        (editable source)
// Run: osascript -e 'tell application "Adobe Illustrator 2026" to do javascript file "<this file>"'
#target illustrator
(function () {
    app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
    var root = File($.fileName).parent.parent;
    var IN = 72, TW = 7 * IN, TH = 5 * IN, BL = 0.125 * IN, R = 0.125 * IN;

    function cmyk(c, m, y, k) { var x = new CMYKColor(); x.cyan = c; x.magenta = m; x.yellow = y; x.black = k; return x; }

    // ---- new CMYK document with bleed
    var p = new DocumentPreset();
    p.colorMode = DocumentColorSpace.CMYK; p.units = RulerUnits.Inches;
    p.width = TW; p.height = TH; p.title = 'DKT_Hidden-Fastener-Label_7x5in';
    p.documentBleedLink = true; p.documentBleedOffsetRect = [BL, BL, BL, BL];
    var doc = app.documents.addDocument(DocumentColorSpace.CMYK, p);
    var ab = doc.artboards[0].artboardRect; // [left, top, right, bottom]

    // ---- global swatches
    function gswatch(name, col) {
        var s; try { s = doc.spots.getByName(name); } catch (e) { s = doc.spots.add(); s.name = name; }
        s.colorType = ColorModel.PROCESS; s.color = col;
        var sc = new SpotColor(); sc.spot = s; sc.tint = 100; return sc;
    }
    var ORANGE = gswatch('Deckotech Orange (PMS 172 C)', cmyk(0, 80, 95, 0));
    var BOARD = gswatch('Deckotech Orange - board tint', cmyk(0, 68, 80, 0));
    var PAPER = cmyk(0, 0, 0, 0);
    var cut; try { cut = doc.spots.getByName('CutContour'); } catch (e) { cut = doc.spots.add(); cut.name = 'CutContour'; }
    cut.colorType = ColorModel.SPOT; cut.color = cmyk(0, 100, 0, 0);
    var CUT = new SpotColor(); CUT.spot = cut; CUT.tint = 100;

    // ---- import the vector artwork
    var art = doc.layers[0]; art.name = 'Artwork';
    var svg = File(root + '/artwork/label_print.svg');
    doc.activeLayer = art;
    var grp = art.groupItems.createFromFile(svg); // imports the SVG as editable vector group
    grp.name = 'Label art';
    // place the full-bleed canvas exactly on the bleed box (geometric bounds, not visible bounds)
    var gb = grp.geometricBounds; // [l, t, r, b]
    var sc = (TW + 2 * BL) / (gb[2] - gb[0]) * 100;
    if (Math.abs(sc - 100) > 0.01) grp.resize(sc, sc, true, true, true, true, sc, Transformation.TOPLEFT);
    gb = grp.geometricBounds;
    grp.translate((ab[0] - BL) - gb[0], (ab[1] + BL) - gb[1]);

    // ---- map fills to CMYK swatches. Import converts RGB->CMYK approximately, so classify by rank:
    // white (no ink) -> paper; strongest orange -> Deckotech Orange; the lighter orange -> board tint.
    var paths = [];
    function collect(it) {
        if (it.typename === 'GroupItem') { for (var j = 0; j < it.pageItems.length; j++) collect(it.pageItems[j]); return; }
        if (it.typename === 'CompoundPathItem') { for (var k = 0; k < it.pathItems.length; k++) collect(it.pathItems[k]); return; }
        if (it.typename === 'PathItem' && it.filled) paths.push(it);
    }
    collect(grp);
    function ink(c) {
        if (c.typename === 'CMYKColor') return c.cyan + c.magenta + c.yellow + c.black;
        if (c.typename === 'RGBColor') return 765 - (c.red + c.green + c.blue);
        if (c.typename === 'GrayColor') return c.gray;
        return 0;
    }
    var maxInk = 0, i;
    for (i = 0; i < paths.length; i++) maxInk = Math.max(maxInk, ink(paths[i].fillColor));
    var n = { orange: 0, board: 0, paper: 0 };
    for (i = 0; i < paths.length; i++) {
        var v = ink(paths[i].fillColor);
        if (v < maxInk * 0.1) { paths[i].fillColor = PAPER; n.paper++; }
        else if (v > maxInk - 4) { paths[i].fillColor = ORANGE; n.orange++; }
        else { paths[i].fillColor = BOARD; n.board++; }
        paths[i].stroked = false;
    }
    var report = 'paths ' + paths.length + ' orange ' + n.orange + ' board ' + n.board + ' paper ' + n.paper +
        ' | bounds ' + grp.geometricBounds.join(',') + ' | artboard ' + ab.join(',');

    // ---- die line layer (spot "CutContour", overprint, 0.25pt)
    var die = doc.layers.add(); die.name = 'Die line - CutContour (do not print)';
    var rr = die.pathItems.roundedRectangle(ab[1], ab[0], TW, TH, R, R);
    rr.filled = false; rr.stroked = true; rr.strokeColor = CUT; rr.strokeWidth = 0.25; rr.strokeOverprint = true;
    rr.name = 'Die cut 7 x 5 in, R 0.125 in';

    // ---- save editable .ai
    var aiOpts = new IllustratorSaveOptions(); aiOpts.pdfCompatible = true; aiOpts.embedICCProfile = true;
    aiOpts.compatibility = Compatibility.ILLUSTRATOR24;
    Folder(root + '/source').create();
    doc.saveAs(File(root + '/source/DKT_Hidden-Fastener-Label_7x5in.ai'), aiOpts);

    // ---- print PDF
    Folder(root + '/print').create();
    var pdf = new PDFSaveOptions();
    try { pdf.pDFPreset = '[PDF/X-4:2008]'; } catch (e) {}
    pdf.compatibility = PDFCompatibility.ACROBAT7;
    pdf.trimMarks = false; // label printers want bleed + CutContour only; marks would knock into the bleed
    pdf.registrationMarks = false; pdf.colorBars = false; pdf.pageInformation = false;
    pdf.bleedLink = false; pdf.bleedOffsetRect = [BL, BL, BL, BL];
    pdf.preserveEditability = false; pdf.generateThumbnails = true;
    doc.saveAs(File(root + '/print/DKT_Hidden-Fastener-Label_7x5in_PRINT.pdf'), pdf);
    doc.close(SaveOptions.DONOTSAVECHANGES);
    return report;
})();
