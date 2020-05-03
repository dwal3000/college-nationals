var adZones = Array();

function getAd(AdZoneId, AdId, divAdZone) {
    adZones[AdZoneId] = divAdZone;

    $.ajax({
        type: 'GET',
        cache: false,
        url: '/ajax/AdAjax.aspx',
        processData: true,
        data: 'Source=ads&AdId=' + AdId + '&AdZoneId=' + AdZoneId,
        contentType: 'application/x-www-form-urlencoded',
        dataType: 'text',
        success: function(result, textStatus) {
            getAdCallback(result);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            //alert(errorThrown);
        }
    });

}

function getAdCallback(text) {
    var AdZoneId, AdText, aText;

    aText = text.split("|");
    AdZoneId = aText[0];
    AdText = aText[1];

    var divAdZone = adZones[AdZoneId];

    if (AdText != "no_update") {
        if (document.getElementById(divAdZone + '_tmp')) {
            document.getElementById(divAdZone + '_tmp').innerHTML = AdText;
            document.getElementById(divAdZone).innerHTML = document.getElementById(divAdZone + '_tmp').innerHTML;
        } else {
            document.getElementById(divAdZone).innerHTML = AdText;
        }
    }

    //document.getElementById(divAdZone).style.display = 'block';
}