using System;
using System.Collections.Generic;

public class MalformedShortClass
{
    internal List<string> partnerList;

    public void CloseBracketMissing(string key, string value)
    {
        partnerList.Add(key);
        partnerList.Add(value);