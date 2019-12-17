library(httr)
library(DT)
library(ggplot2)
source('global.R')

function(input, output, session) {
  DATA <- get_data()
    
  agg_data <- reactive({
    return(aggregate(amount ~ x, DATA, sum))
  })

  agg_data_categories <- reactive({
    return(aggregate(amount ~ x + name, DATA, sum))
  })
    
  ########################### TAB 1 - PLOTS ###########################

  output$main <- renderPlot({
    agg1 <- aggregate(amount ~ x + sign, DATA, sum)
    ggplot(data = agg1) +
        geom_bar(aes(x = x, y=amount, fill=as.factor(sign), group=x), position = "dodge", stat = "identity") +
        geom_line(data=agg_data(), aes(x=x, y=amount, group=1), color='#FF7F00', size=3) + 
        theme(legend.position='none') +
        scale_fill_brewer(palette='Paired') +
        scale_y_continuous(breaks=seq(-10000, 100000, 1000)) +
        labs(x='', y='')
  })
    
  output$stats <- renderTable({
       tail(aggregate(amount ~ year+month, DATA, sum), 12)
       })
    
  output$stats2 <- renderTable({
       tail(aggregate(amount ~ year, DATA, sum), 3)
       })
    
  output$categories <- renderPlot({
    agg1 <- agg_data_categories()
    if(input$type == 'Wydatki'){
        agg1 <- agg1[agg1$amount<0,] 
        colors <- RColorBrewer::brewer.pal(11, 'Paired')
        names(colors) <- c('Rachunki', 'Zakupy',
                           'Paliwo i transport', 'Auto', 
                           'Dzieci', 'Prezent', 
                           'Sport i relaks', 
                           'Przyjemności i jedzenie na mieście',
                           'Sprzęty domowe', 'Inne wydatki',
                           'Podatki')
    }else{
        agg1 <- agg1[agg1$amount>0,]
        colors <- RColorBrewer::brewer.pal(3, 'Paired')
        names(colors) <- c('Kasia', 'Hepterakt', 'Inne dochody')
    }
      
      
    if(!(any('*' %in% input$cat))){
        agg1 <- agg1[agg1$name %in% input$cat,]
        agg1$name <- factor(agg1$name, levels=input$cat)
    }
    ggplot(agg1) + geom_area(aes(x=x, y=I(abs(amount)), fill=name, group=name),
                                                  position='stack') + 
    theme(axis.text.x = element_text(angle = 90)) +
    scale_fill_manual(values=colors) +
    labs(fill='Kategoria', x='', y='') + 
    scale_y_continuous(breaks=seq(-10000, 100000, 500))
  })
  
  ########################### TAB 2 - DATA ###########################
  observeEvent(input$deletePressed, {
      url <- sprintf('%s/entries/%s', URL, input$deletePressed)
      r <- httr::DELETE(url)
      message(url)
      session$reload()
      })
    
  output$data <- renderDataTable({
      idx <- which(names(DATA) %in% c('year', 'month', 'x'))
      df <- DATA[,-idx]
      df <- df[rev(order(df$date)),]
      ButtonColumns(df, '')
      })


}

