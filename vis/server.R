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


      observe({
          if(input$type == 'Wydatki'){
              choices <- c(as.character(CATEGORIES[[1]]), '*')
              selected_choices <- c('Rachunki','Zakupy','Paliwo i transport')
          }else{
              choices <- c(as.character(CATEGORIES[[-1]]), '*')
              selected_choices <- choices[1:3]
          }
        updateSelectInput(session, 'cat', 'Wybierz kategorie:',
                          choices = choices, selected=selected_choices)
  })
  output$categories <- renderPlot({
      agg1 <- agg_data_categories()
        if(input$type == 'Wydatki'){
            colors <- RColorBrewer::brewer.pal(11, 'Paired')
            names(colors) <- c('Rachunki', 'Zakupy',
                               'Paliwo i transport', 'Auto',
                               'Dzieci', 'Prezent',
                               'Sport i relaks',
                               'Przyjemności i jedzenie na mieście',
                               'Sprzęty domowe', 'Inne wydatki',
                               'Podatki')
        }else{
            colors <- RColorBrewer::brewer.pal(3, 'Paired')
            names(colors) <- c('Kasia', 'Hepterakt', 'Inne dochody')
        }

        if(any('*' %in% input$cat)){
            idx = ifelse(input$type=='Wydatki', 1, -1)
            categories <- as.character(CATEGORIES[[idx]])
        }else{
            categories <- input$cat
        }

      agg <- do.call('rbind', c(sapply(as.character(agg1$x), function(x)
                                      sapply(as.character(agg1$name), function(y)
                                          list(c(x,y)) ))))
      colnames(agg) <- c('x', 'name')
      agg <- merge(agg, agg1, by=c('x', 'name'), how='left', all=TRUE)
      agg[is.na(agg)] <- 0
      agg = agg[!duplicated(agg),]
      agg <- agg[as.character(agg$name) %in% categories,]
    ggplot(agg) + geom_area(aes(x=x, y=I(abs(amount)), fill=name, group=name),
                                                  position='stack') + 
    theme(axis.text.x = element_text(angle = 90)) +
    scale_fill_manual(values=colors) +
    labs(fill='Kategoria', x='', y='') + 
    scale_y_continuous(breaks=seq(0, 100000, 500))
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

