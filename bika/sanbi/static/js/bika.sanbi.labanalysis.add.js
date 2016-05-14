function CustomLabAnalysisAddView(){
    var biospecimensFd = '#archetypes-fieldname-Biospecimens';

    this.load = function(){
        console.log('salam');
        // disable browser auto-complete
        $('input[type=text]').prop('autocomplete', 'off');
        init();
        applyStyles();
    }
    function init() {}
    function applyStyles() {
        $(biospecimensFd)
            .css('border', '1px solid #cfcfcf')
            .css('background-color', '#efefef')
            .css('padding', '10px')
            .css('margin-bottom', '20px');
    }
}