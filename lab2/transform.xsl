<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:template match="/">
    <html>
      <head>
        <title>Каталог товаров</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .in-stock { color: green; }
          .out-of-stock { color: red; }
        </style>
      </head>
      <body>
        <h1>📦 Каталог товаров</h1>
        <table>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Цена (руб.)</th>
            <th>Категория</th>
            <th>Наличие</th>
          </tr>
          <xsl:for-each select="catalog/product">
            <tr>
              <td><xsl:value-of select="@id"/></td>
              <td><xsl:value-of select="name"/></td>
              <td><xsl:value-of select="format-number(price, '#,##0.00')"/></td>
              <td><xsl:value-of select="category"/></td>
              <td>
                <xsl:choose>
                  <xsl:when test="in_stock='true'">
                    <span class="in-stock">✓ В наличии</span>
                  </xsl:when>
                  <xsl:otherwise>
                    <span class="out-of-stock">✗ Нет в наличии</span>
                  </xsl:otherwise>
                </xsl:choose>
              </td>
            </tr>
          </xsl:for-each>
        </table>
        <p>Всего товаров: <strong><xsl:value-of select="count(catalog/product)"/></strong></p>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>