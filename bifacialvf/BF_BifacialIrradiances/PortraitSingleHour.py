#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 14:31:48 2017

@author: sayala
Sara MacAlpine edited 7/28/2017.  
Includes passing interpolation parameters to this routine instead of making matlab call each iteration
Also updated to include more than 6 sensors ("numsens"), as we had 9
Interpolation fixed to flip some values to be interpolated - there was some sort of discrepancy
between the function in the original matlab code and how it behaved when translated to python
I think it was the "unique" function in my matlab 2009 spitting out cols rather than rows.

Takes in Tamb and Vwind and calcs Tcell using Sandia temperature model.   
One could take temperature model from pvlib instead!
"""


import numpy as np    
from scipy.interpolate import interp1d
import math


#def PortraitSingleHour(IVArraySi,BilinearParamsSi, FrontIrradiance, RearFractions, interpolA):
def PortraitSingleHour(FrontIrradiance, RearIrradiance, Tamb, Vwind, numsens, interpolA,IVArray,beta_voc_all,m_all,bee_all):
    #This is just to gauge the effects of irradiance nonuniformity o the backside of 
    #bifacial Si PV Modules
    #Inputs are IVArraySi, which is a multidimensional array of module voltages
    #at currents from 0:.001:Ilim for each temperature-irradiance pair 
    #and BilinearParamsSi, which is used in the bilinear interpolation model to
    #find the I-V curve at actual irradiance and temperature.
    #(these are generated by make_IV_array and make_array_bilinear
    # clear Pmax*
    #This is at the module level because the system is assumed unshaded and with long rows so irradiance is constant in the module X plane.  

    global PmaxUnmatched
    global PmaxIdeal
    
    PmaxUnmatched=0;
    PmaxIdeal=0;
    
    
    NumStrings=1; #It's a single module!
    
    # Get effective front side irradiance (these could be automated inputs)
   # RearIrradiance=FrontIrradiance*np.ones(len(RearFractions))*RearFractions;
    #EffectiveIrradiance=FrontIrradiance*np.ones(len(RearIrradiance))+RearIrradiance;
    EffectiveIrradiance=[x + y for x, y in zip(FrontIrradiance, RearIrradiance)];
    AvgIrradiance=np.mean(EffectiveIrradiance);
    #print "AVG:  " , AvgIrradiance
    EffectiveIrradiance=np.concatenate((EffectiveIrradiance, [AvgIrradiance]),axis=0)
    #print "Effective Irradiance",EffectiveIrradiance


    
    # Now need panel I-V characteristics 
    # This matrix is rows=irradiances (20,50,100...1100,1200), columns =
    # temperature (0-100, steps of 5), and each entry is voltages at currents
    # (currents are 0 to Ilim in steps of 0.01)
    
   
    
    
    # [a b c d]=size(IVArraySi)  #Ilim - 11A
    Ilim=11;
    
    # This shows the irradiances & temperatures that are used
    RefRads=[10, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200];
    
    # RefTemps=-10:5:100;
    RefTemps=[]
    foo=-10
    while foo<=100:
        RefTemps.append(foo)
        foo=foo+5
    
    # RefCurs=0:0.01:Ilim;
    RefCurs=[]    
    foo = 0
    while foo<=Ilim:
        RefCurs.append(foo)
        foo=foo+0.01        
    
    
    # These are for most accurate interpolation.  One could do 0.01A instead
    
    # ManyCurs=0:0.001:Ilim;
    ManyCurs=[]
    foo = 0
    while foo<=Ilim:
        ManyCurs.append(foo)
        foo=foo+interpolA
    
    newX=[]
    foo=-10
    while foo<=600:
        newX.append(foo)
        foo=foo+1
        
    currents=len(ManyCurs);
    #123 WHY IS THERE A J LOOP 1:1????
    #for j=1:1
    
    #123 WHATS UP WITH THIS ASSIGNMENT THAT WAS COMMENTED OUT IN THE ORIGINAL SARAH'S CODE? 
    #i=YearArray(j)
    
    j=0
    i=j
    Tcell=[]
    
    # Get the bilinear interpolated temperature and irradiance points
    # There are 6 cell groupings to consider and 7th is the average
    for s in range (0,numsens):   # There are numsens cell groupings to consider and extra is the average
     
       #Need the cell temperatures - Sandia temperature model!
       a=-3.56;
       b=-0.0750;
       dT=3;
       Tback=EffectiveIrradiance[s]*math.exp(a+b*VWind)+Tamb;
       Tcell.append(Tback+EffectiveIrradiance[s]/1000*dT);
       
       # Just in case.... 
       if EffectiveIrradiance[s]<=10:
           EffectiveIrradiance[s]=10.1
           
       if EffectiveIrradiance[s]>=1199:
           EffectiveIrradiance[s]=1199
       
       if Tcell[s]<=-9.9:
           Tcell[s]=-9.9
           
       if Tcell[s]>=99.9:
           Tcell[s]=99.9               
       
    # Now I have this hour's irradiance and temperature data in
    # EffectiveIrradiance and Tcell.   Need to get the I-V curves for each
    # cell group (since it's portrait there are 6 cell groups per byp)
    # The 7th is the average
    
     
    # This is bilinear interpolation from W. Marion 2004 paper
    d = -1
    CellStripIVs=[]
    s=0
    
    ### BILINEAR INTERPOLATION LOOP
    for s in range (0,numsens):
        
        #-print " "
        #-print " "
        #-print " ******************************"
        #-print "LOOP NUMBER ", s
    
    
        d=d+1;
        sgnvec=np.sign(RefRads-EffectiveIrradiance[s]);
        #[nouse,indR] = min(abs(RefRads-EffectiveIrradiance[s]));
        nouse = min(abs(RefRads-EffectiveIrradiance[s]))
        indR = np.argmin(abs(RefRads-EffectiveIrradiance[s]))
        
        if sgnvec[indR]<0:   #The index found (closest) is on the low side, so the reference is the one
            indRlo=indR;
            indRhi=indR+1;
            Rparam=indR;
            #-print "IndR 1 ", indRlo, indRhi, Rparam
        
        else:
           indRlo=indR-1;
           indRhi=indR;
           Rparam=max(1,indR-1);
           #-print "IndR 2 ", indRlo, indRhi, Rparam
        
         
        
        sgnvec=np.sign(RefTemps-Tcell[s]*np.ones(len(RefTemps)));
        # [nouse,indT] = min(abs(RefTemps-Tcell(s)));
        nouse = min(abs(RefTemps-Tcell[s]*np.ones(len(RefTemps))))
        indT = np.argmin(abs(RefTemps-Tcell[s]*np.ones(len(RefTemps))))
        
        if sgnvec[indT]<0:   #The index found (closest) is on the low side
            indTlo=indT;
            indThi=indT+1;
            Tparam=indT;
            #-print "Tparam 1 ", indTlo, indThi, Tparam
        else:
           indTlo=indT-1;
           indThi=indT;
           Tparam=max(1,indT-1);    
           #-print "Tparam 2 ", indTlo, indThi, Tparam
        
        # now I have Thi, Tlo, Rhi, Rlo
        ref_currents=len(RefCurs);
        
        RadHi=RefRads[indRhi];
        RadLo=RefRads[indRlo];
        RadRef=RefRads[indR];
        TempHi=RefTemps[indThi];
        TempLo=RefTemps[indTlo];
        TempRef=RefTemps[indT];
        
        #-print ""
        #-print "Results from SGNVec"
        #-print indRhi, indRlo, indR, indThi, indTlo, indT
        #-print RadHi, RadLo, RadRef, TempHi, TempLo, TempRef
            
        # Now get the individual panel info at those irradiance and temperatures
        # The past part was just operating conditions! Now I need the behavior of each module type  
        
        #123 WHAT IS THIS FOR? Commented Out in the Original Code, not translated yet.
        #for pan=1:2
            #IVArray=IVArraySi; BilinearParams=BilinearParamsSi;
        #   else IVArray=IVArrayInGaP; BilinearParams=BilinearParamsInGaP;
        #  end
    
        
        IVRloTlo=IVArray[0,indRlo,indTlo,:]
        IVRhiTlo=IVArray[0,indRhi,indTlo,:]
        IVRloThi=IVArray[0,indRlo,indThi,:]
        IVRhiThi=IVArray[0,indRhi,indThi,:]
        #print "IVRLOTLO:   ",IVRloTlo
        #print "IVRLOTHI:   ",IVRloThi
        #print "IVRHITLO:   ",IVRhiTlo
        #print "IVRHITHI:   ",IVRhiThi
        
        #-print "Compaing IV ARRAYS"
        #-print "IVRloTlo", IVRloTlo[0], IVRloTlo[99], IVRloTlo[499], IVRloTlo[len(IVRloTlo)-1]
        #-print "IVRhiTlo", IVRhiTlo[0], IVRhiTlo[99], IVRhiTlo[499], IVRhiTlo[len(IVRhiTlo)-1]
        #-print "IVRloThi", IVRloThi[0], IVRloThi[99], IVRloThi[499], IVRloThi[len(IVRloThi)-1]
        #-print "IVRhiThi", IVRhiThi[0], IVRhiThi[99], IVRhiThi[499], IVRhiThi[len(IVRhiThi)-1]
        
            
        #123 FIXED BUT NOT ORIGINAL METHOD
        # Created a new matrices for beta_voc_all, m_all and bee_all (that get loaded before this
        # and we call the values here. Originally they were part of BilinearParams matrix
        # but I was not able to access the values directly (arrays inside of an object...)                                                  
        # Maybe fix? Not prioritary though
        
        #beta_voc=BilinearParams{1}.betas(Rparam,Tparam);  
        #m=BilinearParams{1}.ms(Rparam,Tparam);
        #bee=BilinearParams{1}.bs(Rparam,Tparam);
        beta_voc = beta_voc_all[Rparam][Tparam]
        m = m_all[Rparam][Tparam]
        bee= bee_all[Rparam][Tparam]
    
        # If matrix not available at least for Yingli's demo scenario this are the values:
        #    if s==0:        
        #        beta_voc = -0.0040166627
        #        m = 0.0007680563
        #        bee = 0.0548576452
        #        
        #    if s==1:        
        #        beta_voc = -0.0037578270
        #        m = 0.0006672973
        #        bee = 0.0622129443
        #        
        #        
        #    if s==2:
        #        beta_voc = -0.0037578270
        #        m = 0.0006672973
        #        bee = 0.0622129443
        #
        #    if s==3:        
        #        beta_voc = -0.0037578270
        #        m = 0.0006672973
        #        bee = 0.0622129443
        #        
        #    if s==4:        
        #        beta_voc = -0.0037578270
        #        m = 0.0006672973
        #        bee = 0.0622129443
        #        
        #    if s==5:        
        #        beta_voc = -0.0038501193
        #        m = 0.0007081762
        #        bee = 0.0589041503
        #        
        #    if s==6:        
        #        beta_voc = -0.0037715930
        #        m = 0.0006808530
        #        bee = 0.0605435439
    
       
        # Translate the first set of curves:  this is just Voc
        VocRhiTlo=IVRhiTlo[0];
        VocRhiThi=IVRhiThi[0];
        VocRloTlo=IVRloTlo[0];
        VocRloThi=IVRloThi[0];
            
        VocRhiTc=IVArray[0,indRhi,indT,0]*(1+beta_voc*(Tcell[s]-TempRef))*(1+(m*Tcell[s]+bee)*math.log(RadHi/RadHi));
        VocRloTc=IVArray[0,indRlo,indT,0]*(1+beta_voc*(Tcell[s]-TempRef))*(1+(m*Tcell[s]+bee)*math.log(RadLo/RadLo));
        IVRhiTc=IVRhiThi+(IVRhiTlo-IVRhiThi)*(VocRhiTc-VocRhiThi)/(VocRhiTlo-VocRhiThi);
        IVRloTc=IVRloThi+(IVRloTlo-IVRloThi)*(VocRloTc-VocRloThi)/(VocRloTlo-VocRloThi);
        #print "IVRhiTc:   ",IVRhiTc
        #print "IVRloTc:   ",IVRloTc
        
        #-print ""
        #-print "First Set of Curves Translation"
        #-print "VocRhiTc", VocRhiTc, "VocRloTc", VocRloTc
        #-print "IVRhiTc", IVRhiTc[0], IVRhiTc[99], IVRhiTc[499], IVRhiTc[len(IVRhiTc)-1]
        #-print "IVRloTc", IVRloTc[0], IVRloTc[99], IVRloTc[499], IVRloTc[len(IVRloTc)-1]
        
        # Take the new curves at Tc and interpolate so they have the same voltages
        IVRhiTc_Iinterp=interp1d(IVRhiTc,RefCurs, kind='linear', bounds_error=False, fill_value=0)(newX)
        IVRloTc_Iinterp=interp1d(IVRloTc,RefCurs, kind='linear', bounds_error=False, fill_value=0)(newX)
        #print "IVRhiTc_Iinterp:   ",IVRhiTc_Iinterp
        #print "IVRloTc_Iinterp:   ",IVRloTc_Iinterp
        
        #-print ""
        #-print "First Set of Curves Translation"
        #-print "Interpolation IVRhiTc_Iinterp", IVRhiTc_Iinterp[0], IVRhiTc_Iinterp[9], IVRhiTc_Iinterp[19], IVRhiTc_Iinterp[29]
        #-print "Interpolation IVRloTc_Iinterp", IVRloTc_Iinterp[0], IVRloTc_Iinterp[9], IVRloTc_Iinterp[19], IVRloTc_Iinterp[29]
           
        
        # Now the Isc translation
        IscLo=IVRloTc_Iinterp[10];
        IscHi=IVRhiTc_Iinterp[10];
        IscTc=EffectiveIrradiance[s]/RadLo*IscLo; #temperatures are the same already
        IReal=IVRloTc_Iinterp+(IVRhiTc_Iinterp-IVRloTc_Iinterp)*(IscTc-IscLo)/(IscHi-IscLo);
        
        #-print ""
        #-print "ISC Translation"
        #-print "IReal", IReal[0], IReal[9], IReal[19], IReal[39]
        
        
        # Now put it back to RefCurs instead of voltage-wise
        [Uni,uniind] = np.unique(IReal, return_index=True)
           
        p=np.polyfit(Uni[1:3],[newX[uniind[1]],newX[uniind[2]]],1);
        VocReal=np.polyval(p,0);
        
        #-print ""
        #-print "sometihing else?"
        #-print "Uni", Uni[0], Uni[9], Uni[19], Uni[39]
        #-print "uniind", uniind[0], uniind[9], uniind[19], uniind[39]
        #-print "p", p
        #-print "VocReal", VocReal
        
             
        #123 Matlab code has a flipud here, but it doesn't flip it.... 
        # Original UniCurs starts at index 2 instead of 1, flips it and adds a 0 at the end.
        # Why is it this necessary when the first UniCurs is 0?? 
        UC=Uni[0:len(Uni)]
        UniCurs=UC[::-1]; # <-- replicates that behavior in python
        
        #UniCurs=np.flipud(Uni); 
        
        #123 Matlab issue? 
        # IndUni=fliplr(uniind(2:length(uniind))); <-- doens't do anything!!?? 
        # Python This is the line that should flip
        
        IndUni=np.flipud(uniind[1:len(uniind)]);
       
        # Since the original code doesn't flipwe are using the next line:
        #IndUni=uniind[1:len(uniind)]  
        
        
        #-print ""
        #-print "Flips"
        #-print "Uni", UniCurs[0], UniCurs[9], UniCurs[19], UniCurs[len(UniCurs)-1]
        #-print "IndUni", IndUni[0], IndUni[9], IndUni[19], IndUni[len(IndUni)-1]
        
        UniVee=np.flipud(newX[IndUni[len(IndUni)-1]:IndUni[0]:-1])
        UniVee=np.insert(UniVee,0,values=newX[IndUni[0]])
      
        UniVee=[float(iii) for iii in UniVee]
       
        UniVee=np.insert(UniVee,len(UniVee),values=VocReal)
      
                    
        PanVolt=interp1d(UniCurs,UniVee, kind='linear',  bounds_error=False, fill_value=-10000)(ManyCurs)
        
        #-print ""
        #-print "UniVee and PanVolt"
        #-print "UniVee", UniVee[0], UniVee[1], UniVee[2], UniVee[len(UniVee)-1]
        #-print "PanVolt", PanVolt[0], PanVolt[19], PanVolt[29], PanVolt[99]
           
            
            #PanMaxPowers(pan)=max(ManyCurs.*PanVolt);     
        CellStripIVs.append(PanVolt/numsens);
        
        #-print "CellStripIVs", CellStripIVs[d][0], CellStripIVs[d][19], CellStripIVs[d][29], CellStripIVs[d][99]
        
        ### END OF BILINEAR INTERPOLATION LOOP
    
    
    
    # BypassDiodeLevelIVCUrves 
    # These are voltages at each current!
    # Ignoring CellStripsIVs[0] because it's empty array
    
    # Array size by now= CellStripIVs[6][11000]
    #print "CSIV:  ",CellStripIVs
    BypIVs=np.sum(CellStripIVs,axis=0)/3;
    #print "BIV  ",BypIVs
    #123 Is there a smarter way to do this: BypIVs=max(BypIVs,-0.7); ??
    #YES!!
    #for foo in range (0,len(BypIVs)):
    #    if BypIVs[foo]<-0.7:
    #        BypIVs[foo]=-0.7
    low_values_indices = BypIVs < -0.7  # Where values are low
    BypIVs[low_values_indices] = -0.7             
    
    ModIVs=BypIVs*3;
    #print "CSIV=  ",CellStripIVs

    
    # GOOD TO HERE!!!   #123 This is Sarah's Code what does she mean? 
    
    # Now get the max possible power
    Pmax=[]
    for s in range (0,numsens):
        PCellRow=[a*b for a,b in zip(ManyCurs,CellStripIVs[s])]
        #print "MC:   ",ManyCurs
        #print "CellSt:  ",CellStripIVs[s]
        #print "PCR=  ", PCellRow
        Pmax.append(np.max(PCellRow));
    
    PmaxIdeal=sum(Pmax)
        
    # Now Module IV
    MIV=[a*b for a,b in zip(ManyCurs,ModIVs)]
    PmaxUnmatched=np.max(MIV)
     
    #PmaxLoss=(PmaxUnmatched-PmaxIdeal)/PmaxIdeal
     
    # Now Avg
    PmaxAvg=np.average(Pmax)*numsens
    
    #123 This is the original line but, it's not fiding any real min
    #PmaxMin=min(Pmax[s]*6) <- desn't make sense
    # Maybe it's this what it wanted?
    #PmaxMin=min(Pmax)*6
    

    return PmaxIdeal, PmaxUnmatched, PmaxAvg;


#class Program:
#    FrontIrradiance=930;
#    RearFractions=[0.83, 0.165, 0.13, 0.105, 0.105, 0.41];
#    interpolA = 0.001  # More accurate interpolation. Do 0.01 as an option.
#    