from models.models import Topic, TopicInTopic


def visual(vis, params):
    topics = Topic.objects.filter(
        model=vis.model,
        layer=vis.model.layers_count).order_by("spectrum_index")
    topic_names = [truncate(topic.top_words_list(count=20))
                   for topic in topics]
    N = len(topic_names)
    colors = [wavelength_to_rgb(750 - i * (300 / (N - 1))) for i in range(N)]
    topic_names = ["<span style='color:%s'>%d. %s</span>" %
                   (colors[i], i + 1, topic_names[i])
                   for i in range(N)]
    return (("<div style='font-family: Geneva, "
             "Arial, Helvetica, sans-serif;'>") +
            "<br>".join(topic_names) + "</div>")


def truncate(string, length=100):
    s = string + ','
    best_comma = -1
    for i in range(len(s)):
        if s[i] == ',' and i < length:
            best_comma = i
    return s[0:best_comma]


# Source: http://www.efg2.com/Lab/ScienceAndEngineering/Spectra.htm
def wavelength_to_rgb(wlength):
    gamma = 0.80
    intensity_max = 255

    def adjust(color, factor):
        if color == 0:
            return 0
        else:
            return round(intensity_max * ((color * factor) ** gamma))

    if wlength < 380 or wlength > 780:
        R = G = B = 0
    elif wlength < 440:
        R = -(wlength - 440.0) / (440.0 - 380.0)
        G = 0.0
        B = 1.0
    elif wlength < 490:
        R = 0
        G = (wlength - 440.0) / (490.0 - 440.0)
        B = 1.0
    elif wlength < 510:
        R = 0.0
        G = 1.0
        B = -(wlength - 510.0) / (510.0 - 490)
    elif wlength < 580:
        R = (wlength - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif wlength < 645:
        R = 1.0
        G = -(wlength - 645) / (645 - 580)
        B = 0.0
    elif wlength <= 780:
        R = 1.0
        G = 0.0
        B = 0.0

    # Let the intensity fall off near the vision limits
    if wlength < 380 or wlength > 780:
        factor = 0
    elif wlength < 420:
        factor = 0.3 + 0.7 * (wlength - 380) / (420 - 380)
    elif wlength < 700:
        factor = 1
    elif wlength <= 780:
        factor = 0.3 + 0.7 * (780 - wlength) / (780 - 700)

    R = adjust(R, factor)
    G = adjust(G, factor)
    B = adjust(B, factor)
    return "#%0*x%0*x%0*x" % (2, R, 2, G, 2, B)
