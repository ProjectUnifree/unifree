using System;
using System.Collections.Generic;

public class AdjustAdRevenue
{
    internal string source;
    internal double? revenue;
    internal string currency;
    internal int? adImpressionsCount;
    internal string adRevenueNetwork;
    internal string adRevenueUnit;
    internal string adRevenuePlacement;
    internal List<string> partnerList;
    internal List<string> callbackList;


    public AdjustAdRevenue(string source)
    {
        this.source = source;
#if UNITY_EDITOR
        this.callbackList = []
#endif

    }

#region Revenue
    public void setRevenue(double amount, string currency)
    {
        this.revenue = amount;
        this.currency = currency;
    }
#endregion

    public void setAdImpressionsCount(int adImpressionsCount)
    {
        this.adImpressionsCount = adImpressionsCount;
    }

    public void setAdRevenueNetwork(string adRevenueNetwork)
    {
        this.adRevenueNetwork = adRevenueNetwork;
    }
}